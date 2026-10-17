import {test, expect, Page} from '@playwright/test';

const file = (name: string, id = 1) => ({id, file_name: name, parsed_data: {technical_skills: ['Python']}});
const report = {id: 10, resume_id: 1, job_role: 'Economist', experience_level: 'Junior', analysis_data: {matched_skills: [], match_percent: 0}, gap_analysis: {missing_skills: []}};
async function auth(page: Page) {
  await page.addInitScript(() => { if (!localStorage.getItem('careermind_token')) localStorage.setItem('careermind_token','account-one'); });
  await page.route('**/api/v1/auth/me', route => route.fulfill({json: {id: route.request().headers().authorization?.includes('account-two') ? 2 : 1, email: 'test@example.com'}}));
}

test('independent workspace retries preserve typed preferences and avoid duplicate loading', async ({page}) => {
  await auth(page); let resumes = 0; let reports = 0;
  await page.route('**/api/v1/resume/my-resumes', route => route.fulfill(++resumes === 1 ? {status:503,json:{detail:'Unavailable'}} : {json:[file('saved.docx')]}));
  await page.route('**/api/v1/analysis/reports?limit=1', route => route.fulfill(++reports === 1 ? {status:503,json:{detail:'Unavailable'}} : {json:[report]}));
  await page.goto('/dashboard');
  await expect(page.getByRole('button',{name:'Retry saved resumes'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Retry saved report'})).toBeVisible();
  expect(resumes).toBe(1); expect(reports).toBe(1);
  await page.getByLabel('1. Choose your target role').fill('Product Designer');
  await page.getByRole('button',{name:'Retry saved resumes'}).click();
  await expect(page.getByLabel('Or use a saved resume')).toHaveValue('1');
  await page.getByRole('button',{name:'Retry saved report'}).click();
  await expect(page.getByRole('button',{name:'Retry saved report'})).toHaveCount(0);
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('Product Designer');
  expect(resumes).toBe(2); expect(reports).toBe(2);
});

test('refresh failure preserves the last loaded resume and retry recovers', async ({page}) => {
  await auth(page);let count=0;
  await page.route('**/api/v1/resume/my-resumes',route=>route.fulfill(++count===2 ? {status:503,json:{detail:'Unavailable'}} : {json:[file(count===1?'first.docx':'updated.docx')]}));
  await page.goto('/dashboard/resume');
  await expect(page.getByRole('button',{name:'first.docx',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Refresh saved resumes'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('last loaded resumes');
  await expect(page.getByRole('button',{name:'first.docx',exact:true})).toBeVisible();
  await expect(page.getByText('No Resume Parsed Yet')).toHaveCount(0);
  await page.getByRole('button',{name:'Retry saved resumes'}).click();
  await expect(page.getByRole('button',{name:'updated.docx',exact:true})).toBeVisible();
});

test('late resume data from a prior account cannot populate a new session', async ({page,context}) => {
  await auth(page);
  let release: () => void = () => {};
  const held = new Promise<void>(resolve => { release=resolve; });
  let started: () => void = () => {};
  const requested = new Promise<void>(resolve => { started=resolve; });
  await page.route('**/api/v1/resume/my-resumes', async route => {
    const old = route.request().headers().authorization?.includes('account-one');
    if(old) { started(); await held; }
    await route.fulfill({json:[file(old?'private-old.docx':'new-account.docx',old?1:2)]}).catch(()=>{});
  });
  await page.goto('/dashboard/resume');await requested;
  const second = await context.newPage();
  await second.route('**/api/v1/**', route => route.fulfill({json:{id:1,email:'test@example.com'}}));
  await second.goto('/does-not-exist');
  await second.evaluate(()=>localStorage.setItem('careermind_token','account-two'));
  await expect(page.getByRole('button',{name:'new-account.docx',exact:true})).toBeVisible();
  release();
  await expect(page.getByRole('button',{name:'private-old.docx',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'new-account.docx',exact:true})).toBeVisible();await second.close();
});

test('report list and detail errors do not masquerade as an empty account', async ({page}) => {
  await auth(page);let lists=0;let details=0;
  await page.route('**/api/v1/analysis/report-summaries?limit=20', route=>route.fulfill(++lists===1 ? {status:503,json:{detail:'List unavailable'}} : {json:{items:[{...report,created_at:'2026-10-16'}],next_before:null}}));
  await page.route('**/api/v1/analysis/reports/10', route=>route.fulfill(++details===1 ? {status:503,json:{detail:'Detail unavailable'}} : {json:report}));
  await page.goto('/dashboard/reports');
  await expect(page.getByRole('button',{name:'Retry report list',exact:true})).toBeVisible();
  await expect(page.getByText('No reports yet.',{exact:false})).toHaveCount(0);
  await page.getByRole('button',{name:'Retry report list',exact:true}).click();
  await expect(page.getByRole('button',{name:'Retry report',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Retry report',exact:true}).click();
  await expect(page.getByRole('link',{name:'Open action plan'})).toHaveAttribute('href','/dashboard/roadmap?report=10');
  expect(lists).toBe(2);expect(details).toBe(2);
});


test('a late refresh cannot hide a newly uploaded resume', async ({page}) => {
  await auth(page);let calls=0;let release: () => void = () => {};
  const held = new Promise<void>(resolve => {release=resolve;});
  let started: () => void = () => {};
  const pending = new Promise<void>(resolve=>{started=resolve;});
  await page.route('**/api/v1/resume/my-resumes',async route=>{
    if(++calls===2) {started();await held;}
    await route.fulfill({json:[file('old.docx')]}).catch(()=>{});
  });
  await page.route('**/api/v1/resume/upload',route=>route.fulfill({status:201,json:file('new-upload.docx',2)}));
  await page.goto('/dashboard/resume');
  await expect(page.getByRole('button',{name:'old.docx',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Refresh saved resumes'}).click();await pending;
  await page.locator('input[type=file]').setInputFiles({name:'new-upload.docx',mimeType:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',buffer:Buffer.from('synthetic upload fixture')});
  await page.getByRole('button',{name:'Use this resume'}).click();
  await expect(page.getByRole('button',{name:'new-upload.docx',exact:true})).toBeVisible();
  release();
  await expect(page.getByRole('button',{name:'new-upload.docx',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Refresh saved resumes'})).toBeEnabled();
});
