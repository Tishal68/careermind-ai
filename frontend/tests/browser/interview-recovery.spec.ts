import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('careermind_token','recovery-test'));
  await page.route('**/api/v1/auth/me',route=>route.fulfill({json:{id:1,email:'test@example.com',target_job_role:'Teacher'}}));
});

test('a lost evaluation response can be recovered after refresh with saved feedback',async({page})=>{
  const feedback={question:'Question one',user_answer:'My actual teaching example',score:80,strengths:['Clear'],mistakes:[],suggested_answer:'Template with [your real example]',next_question:'Question two'};
  let saved=false; const indexes:number[]=[];
  await page.route('**/api/v1/interview/sessions',route=>route.fulfill({json:[{id:8,target_role:'Teacher',created_at:'2026-10-18',completed:false}]}));
  await page.route('**/api/v1/interview/sessions/8',route=>route.fulfill({json:{id:8,history:saved?[{question:'Question one',answer:feedback.user_answer,evaluation:feedback},{question:'Question two',answer:null}]:[{question:'Question one',answer:null}]}}));
  await page.route('**/api/v1/interview/evaluate',async route=>{indexes.push(route.request().postDataJSON().question_index);saved=true;await route.abort('failed');});
  await page.goto('/dashboard/interview');
  await page.getByRole('button',{name:/Resume Teacher/}).click();
  await page.getByLabel('Interview answer').fill(feedback.user_answer);
  await page.getByRole('button',{name:'Submit Answer & Evaluate'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('Interview answer')).toHaveValue(feedback.user_answer);
  await page.reload();await page.getByRole('button',{name:/Resume Teacher/}).click();
  await expect(page.getByRole('heading',{name:/Practice feedback:/})).toBeVisible();
  await page.getByRole('button',{name:'Next question',exact:true}).click();
  await expect(page.getByText('Question two',{exact:true})).toBeVisible();
  await page.getByLabel('Interview answer').fill('Second answer');
  await page.getByRole('button',{name:'Submit Answer & Evaluate'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toBeVisible();
  expect(indexes).toEqual([0,1]);
});

test('coach pins context, sends and clearing to the selected report',async({page})=>{
  const messages:any[]=[];const clears:string[]=[];
  await page.route('**/api/v1/analysis/report-summaries?limit=20',route=>route.fulfill({json:{items:[{id:2,job_role:'Nurse',created_at:'2026-10-18'},{id:1,job_role:'Teacher',created_at:'2026-10-17'}],next_before:null}}));
  await page.route('**/api/v1/chat/**',async route=>{
    const url=new URL(route.request().url()); const id=Number(url.searchParams.get('report_id'));
    if(url.pathname.endsWith('/context')) await route.fulfill({json:{report_id:id,job_role:id===1?'Teacher':'Nurse',file_name:'test.docx',missing_skills:[]}});
    else if(url.pathname.endsWith('/history')) await route.fulfill({json:{messages:[],next_before:null}});
    else if(url.pathname.endsWith('/message')) {messages.push(route.request().postDataJSON());await route.fulfill({json:{id:3,role:'assistant',content:'Selected report advice'}});}
    else {clears.push(url.searchParams.get('report_id')!);await route.fulfill({status:204});}
  });
  await page.goto('/dashboard/coach?report=1');
  await expect(page.getByLabel('Choose the report for this conversation')).toHaveValue('1');
  await expect(page.getByText('Teacher',{exact:true})).toBeVisible();
  await page.getByLabel('Career question').fill('Help me');await page.getByRole('button',{name:'Send message',exact:true}).click();
  await expect(page.getByText('Selected report advice')).toBeVisible();expect(messages[0].report_id).toBe(1);
  await page.getByRole('button',{name:'Clear conversation'}).click();await expect(page.getByText('Selected report advice')).toHaveCount(0);expect(clears).toEqual(['1']);
  await page.getByLabel('Choose the report for this conversation').selectOption('2');
  await expect(page.getByText('Nurse',{exact:true})).toBeVisible();await expect(page).toHaveURL(/report=2/);
  await page.reload();await expect(page.getByLabel('Choose the report for this conversation')).toHaveValue('2');
});

test('coach page displays persistent heading and clear empty state when no reports exist', async ({ page }) => {
  await page.route('**/api/v1/analysis/report-summaries?limit=20', route => route.fulfill({
    json: { items: [], next_before: null }
  }));
  await page.goto('/dashboard/coach');
  await expect(page.getByRole('heading', { level: 1, name: 'Career coach' })).toBeVisible();
  await expect(page.getByRole('heading', { level: 2, name: 'No career reports found' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Analyze a resume to start coaching' })).toBeVisible();
});
