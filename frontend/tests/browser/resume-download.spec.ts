import {test, expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => localStorage.setItem('careermind_token','download-test'));
  await page.route('**/api/v1/auth/me',r => r.fulfill({json:{id:1,email:'download@example.com'}}));
  await page.route('**/api/v1/deployment-info',r => r.fulfill({json:{disposable_demo:false}}));
  await page.route('**/api/v1/resume/my-resumes',r => r.fulfill({json:[{id:1,file_name:'nurse.docx',parsed_data:{}}]}));
});

test('download preserves original bytes and filename', async ({page}) => {
  const bytes = Buffer.from([80,75,3,4,0,255,128,10]);
  await page.route('**/api/v1/resume/session/1/file',r => {
    expect(r.request().headers().authorization).toBe('Bearer download-test');
    return r.fulfill({contentType:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',body:bytes});
  });
  await page.goto('/dashboard/resume');
  const pending = page.waitForEvent('download');
  await page.getByRole('button',{name:'Download nurse.docx',exact:true}).click();
  const downloaded = await pending;
  expect(downloaded.suggestedFilename()).toBe('nurse.docx');
  expect(await readFile((await downloaded.path())!)).toEqual(bytes);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('missing legacy original shows actionable error', async ({page}) => {
  await page.route('**/api/v1/resume/session/1/file',r => r.fulfill({status:404,json:{detail:'This older resume has no stored original. Please upload it again.'}}));
  await page.goto('/dashboard/resume');
  await page.getByRole('button',{name:'Download nurse.docx',exact:true}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Please upload it again');
  await expect(page.getByRole('button',{name:'Download nurse.docx',exact:true})).toBeEnabled();
});
