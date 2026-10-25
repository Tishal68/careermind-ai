import {test, expect} from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => localStorage.setItem('careermind_token', 'resume-flow-test'));
  await page.route('**/api/v1/auth/me', route => route.fulfill({json:{id:1,email:'demo@example.com'}}));
  await page.route('**/api/v1/deployment-info', route => route.fulfill({json:{disposable_demo:true}}));
  await page.route('**/api/v1/resume/my-resumes', route => route.fulfill({json:[{id:1,file_name:'saved.pdf'}]}));
  await page.route('**/api/v1/analysis/reports?limit=1', route => route.fulfill({json:[]}));
});

test('visible chooser supports keyboard, upload and choosing the same file again', async ({page}) => {
  let uploads = 0;
  await page.route('**/api/v1/resume/upload', route => {
    uploads++;
    expect(route.request().headers()['content-type']).toContain('multipart/form-data');
    expect(route.request().postDataBuffer()?.toString()).toContain('sample.pdf');
    return route.fulfill({status:201,json:{id:2,file_name:'sample.pdf',parsed_data:{}}});
  });
  await page.goto('/dashboard');
  await expect(page.getByLabel('Demo storage notice')).toContainText('Accounts, resumes, and reports may reset');
  for (let i = 0; i < 2; i++) {
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button',{name:'Choose resume file (PDF/DOCX)',exact:true}).focus();
    await page.keyboard.press('Enter');
    await (await chooser).setFiles({name:'sample.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4 synthetic UI fixture')});
    await page.getByRole('button',{name:'Use this resume',exact:true}).click();
    await expect(page.getByRole('status')).toContainText('sample.pdf is ready to use.');
  }
  expect(uploads).toBe(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('research retry preserves inputs and reuses its idempotency key', async ({page}) => {
  const keys: string[] = [];
  await page.route('**/api/v1/analysis/research', route => {
    keys.push(route.request().headers()['idempotency-key']);
    return keys.length === 1 ? route.abort('timedout') : route.fulfill({status:202,json:{id:7}});
  });
  await page.route('**/api/v1/analysis/research/7', route => route.fulfill({json:{status:'failed',error:'Synthetic completion'}}));
  await page.goto('/dashboard');
  await page.getByLabel('1. Choose your target role').fill('Registered Nurse');
  await page.getByRole('button',{name:'Research my role match',exact:true}).click();
  await expect(page.getByRole('main').getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('Registered Nurse');
  await page.getByRole('button',{name:'Research my role match',exact:true}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Synthetic completion');
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBeTruthy();
  expect(keys[0]).toBe(keys[1]);
});
