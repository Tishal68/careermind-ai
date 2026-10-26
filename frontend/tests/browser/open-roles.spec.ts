import {test, expect} from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.route('**/api/v1/interview/sessions',route=>route.fulfill({json:[]}));
  await page.addInitScript(() => localStorage.setItem('careermind_token','role-test'));
  await page.route('**/api/v1/auth/me', route => route.fulfill({json:{id:1,email:'roles@example.com',target_job_role:'Registered Nurse'}}));
});

test('settings accepts a custom profession and late settings cannot overwrite typing',async ({page})=>{
  let release: () => void = () => {};
  const held = new Promise<void>(resolve => {release=resolve;});
  let saved = '';
  // A fresh session read must reflect the role persisted by the settings API.
  await page.route('**/api/v1/auth/me', route => route.fulfill({json:{id:1,email:'roles@example.com',target_job_role:saved || 'Registered Nurse'}}));
  await page.route('**/api/v1/user/settings', async route=>{
    if(route.request().method()==='PUT') { saved=route.request().postDataJSON().target_job_role; await route.fulfill({json:{user:{target_job_role:saved}}}); }
    else { await held; await route.fulfill({json:{target_job_role:'Accountant',preferred_ai_model:'configured-model'}}); }
  });
  await page.goto('/dashboard/settings');
  await page.getByLabel('Target Job Role').fill('Occupational Therapist');
  release();
  await expect(page.getByText('configured-model',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Target Job Role')).toHaveValue('Occupational Therapist');
  await page.getByRole('button',{name:'Save Preferences'}).click();
  await expect(page.getByText('CareerMind settings saved successfully.')).toBeVisible();
  expect(saved).toBe('Occupational Therapist');
  await page.route('**/api/v1/resume/my-resumes',route=>route.fulfill({json:[]}));
  await page.route('**/api/v1/analysis/reports?limit=1',route=>route.fulfill({json:[]}));
  await page.getByRole('link',{name:'Role match',exact:true}).click();
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('Occupational Therapist');
});

test('interview submits a non-listed profession',async ({page})=>{
  let role='';
  await page.route('**/api/v1/interview/start',async route=>{
    role=route.request().postDataJSON().target_role;
    await route.fulfill({status:503,json:{detail:'Provider temporarily unavailable'}});
  });
  await page.goto('/dashboard/interview');
  await expect(page.getByLabel('Target job role')).toHaveValue('Registered Nurse');
  await page.getByLabel('Target job role').fill('Museum Conservator');
  await page.getByRole('button',{name:'Start interview'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Provider temporarily unavailable');
  expect(role).toBe('Museum Conservator');
});

test('research starts with the saved professional role',async ({page})=>{
  await page.route('**/api/v1/resume/my-resumes',route=>route.fulfill({json:[]}));
  await page.route('**/api/v1/analysis/reports?limit=1',route=>route.fulfill({json:[]}));
  await page.goto('/dashboard');
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('Registered Nurse');
  await page.getByLabel('1. Choose your target role').fill('वित्त सलाहकार');
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('वित्त सलाहकार');
});
