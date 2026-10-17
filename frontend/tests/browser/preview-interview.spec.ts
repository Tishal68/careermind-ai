import {test,expect} from '@playwright/test';

test.beforeEach(async ({page})=>{
  await page.addInitScript(()=>localStorage.setItem('careermind_token','preview-test'));
  await page.route('**/api/v1/auth/me',route=>route.fulfill({json:{id:1,email:'preview@example.com',target_job_role:'Teacher'}}));
});

test('resume text loads only on request, retries and changes with the selected resume',async ({page})=>{
  let count=0;
  await page.route('**/api/v1/resume/my-resumes',route=>route.fulfill({json:[{id:1,file_name:'first.docx',parsed_data:{}},{id:2,file_name:'second.docx',parsed_data:null}]}));
  await page.route('**/api/v1/resume/session/1/text',route=>route.fulfill(++count===1?{status:503,json:{detail:'Unavailable'}}:{json:{text:'Nursing education <script>unsafe()</script>'}}));
  await page.route('**/api/v1/resume/session/2/text',route=>route.fulfill({json:{text:'Teaching experience'}}));
  await page.goto('/dashboard/resume');
  await expect(page.getByRole('button',{name:'View extracted resume text'})).toBeVisible();expect(count).toBe(0);
  await page.getByRole('button',{name:'View extracted resume text'}).click();
  await page.getByRole('button',{name:'Retry extracted text'}).click();
  await expect(page.getByLabel('Resume text content')).toContainText('<script>unsafe()</script>');
  await page.getByRole('button',{name:'second.docx',exact:true}).click();
  await expect(page.getByLabel('Resume text content')).toHaveCount(0);
  await page.getByRole('button',{name:'View extracted resume text'}).click();
  await expect(page.getByLabel('Resume text content')).toHaveText('Teaching experience');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
});

test('interview keeps answers on failure, separates feedback and completes without duplicate submission',async ({page})=>{
  let evaluations=0, starts=0;
  await page.route('**/api/v1/interview/start',route=>route.fulfill({json:{id:++starts,history:[{question:'Explain a lesson plan.'}]}}));
  await page.route('**/api/v1/interview/evaluate',route=>route.fulfill(++evaluations===1?{status:503,json:{detail:'Please retry'}}:{json:{score:80,user_answer:'My lesson plan',strengths:['Clear objectives'],mistakes:['Add assessment'],suggested_answer:'Include assessment',next_question:evaluations===2?'How do you assess learning?':null}}));
  await page.route('**/api/v1/resume/my-resumes',route=>route.fulfill({json:[]}));
  await page.route('**/api/v1/analysis/reports?limit=1',route=>route.fulfill({json:[]}));
  await page.goto('/dashboard');
  await page.getByRole('link',{name:'Interview practice',exact:true}).click();
  await page.getByRole('button',{name:'Start interview',exact:true}).click();
  await page.getByLabel('Interview answer').fill('My lesson plan');
  await page.getByRole('button',{name:'Submit Answer & Evaluate'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Please retry');
  await expect(page.getByLabel('Interview answer')).toHaveValue('My lesson plan');
  await page.getByRole('button',{name:'Submit Answer & Evaluate'}).click();
  await expect(page.getByText('Clear objectives',{exact:true})).toBeVisible();
  await expect(page.getByText('Add assessment',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Interview answer')).toHaveCount(0);
  await expect(page.getByText('Explain a lesson plan.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Next question',exact:true}).click();
  await expect(page.getByText('How do you assess learning?',{exact:true})).toBeVisible();
  await page.getByLabel('Interview answer').fill('Use formative checks');
  await page.getByRole('button',{name:'Submit Answer & Evaluate'}).click();
  await expect(page.getByRole('status')).toContainText('Interview complete');
  await expect(page.getByRole('button',{name:'Submit Answer & Evaluate'})).toHaveCount(0);
  await page.getByRole('button',{name:'Start a new interview'}).click();
  await page.getByRole('button',{name:'Start interview',exact:true}).click();
  await expect(page.getByLabel('Interview answer')).toHaveValue('');
  expect(evaluations).toBe(3);expect(starts).toBe(2);
});
