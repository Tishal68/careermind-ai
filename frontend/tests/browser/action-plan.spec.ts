import { test, expect, Page } from '@playwright/test';

async function setup(page: Page, failure = '') {
  let saved = false;
  let revision = 1;
  let completed = false;
  await page.addInitScript(() => localStorage.setItem('careermind_token', 'test-session'));
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const respond = (data: unknown, status = 200) => route.fulfill({status, json: data});
    if (path.endsWith('/auth/me')) return respond({id: 1, email: 'test@example.com', full_name: 'Test'});
    if (path.endsWith('/analysis/report-summaries')) return respond({items: [{id: 41, job_role: 'Backend Developer', experience_level: 'Junior', created_at: '2026-10-16'}, {id: 42, job_role: 'Product Designer', experience_level: 'Senior', created_at: '2026-10-15'}], next_before: null});
    if (path.includes('/action-plan')) {
      if (failure === 'load') return respond({detail: 'Plan service unavailable'}, 503);
      const designer = path.includes('/42/');
      const name = designer ? 'Prototyping' : 'SQL';
      if (route.request().method() === 'PATCH') {
        if (failure === 'conflict') return respond({detail: 'This plan changed in another tab. Reload it and try again.'}, 409);
        completed = route.request().postDataJSON().is_completed;
        revision += 1;
      }
      if (route.request().method() === 'POST') saved = true;
      return respond({report_id: designer ? 42 : 41, job_role: designer ? 'Product Designer' : 'Backend Developer', experience_level: designer ? 'Senior' : 'Junior', created: saved, revision, note: 'Completion records activity, not proficiency.',
        milestones: saved ? [{title: 'Learn or demonstrate '+name, focus_topic: name, tasks: [{id: 'p1-t1', task_name: 'Review '+name+' evidence', is_completed: completed}]}] : [],
        projects: saved ? [{id: 'p1', title: 'Evidence exercise: '+name, description: 'A practice suggestion for '+name, required_skills: [name]}] : []});
    }
    return respond([]);
  });
}

test('selected report, keyboard completion and refresh preserve progress', async ({page}) => {
  await setup(page);
  await page.goto('/dashboard/roadmap?report=42');
  await expect(page.getByRole('heading', {name: 'Product Designer', exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Create action plan'}).click();
  const task = page.getByRole('checkbox', {name: 'Review Prototyping evidence'});
  await task.focus(); await page.keyboard.press('Space');
  await expect(page.getByRole('status').filter({hasText: 'Progress saved.'})).toBeVisible();
  await expect(task).toBeChecked();
  await page.reload(); await expect(task).toBeChecked();
  await expect(page.getByRole('heading', {name: 'Evidence exercise: Prototyping'})).toBeVisible();
  await expect(page.getByText('RAG Pipeline', {exact: false})).toHaveCount(0);
  await page.screenshot({path: 'test-results/action-plan-mobile.png', fullPage: true});
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({width, height: 900});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
});

test('failed plan load shows retry without invented projects', async ({page}) => {
  await setup(page, 'load'); await page.goto('/dashboard/projects?report=42');
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Plan service unavailable');
  await expect(page.getByRole('button', {name: 'Reload plan'})).toBeVisible();
  await expect(page.getByRole('heading', {name: 'Practice projects'})).toHaveCount(0);
  await expect(page.getByRole('button', {name: 'Create action plan'})).toHaveCount(0);
});

test('conflicting edit does not falsely check a task or claim saved', async ({page}) => {
  await setup(page, 'conflict'); await page.goto('/dashboard/roadmap');
  await page.getByRole('button', {name: 'Create action plan'}).click();
  await page.getByRole('checkbox').click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('changed in another tab');
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  await expect(page.getByText('Progress saved.', {exact: true})).toHaveCount(0);
});

test('switching report updates plan identity and projects', async ({page}) => {
  await setup(page); await page.goto('/dashboard/projects?report=41');
  await page.getByRole('button', {name: 'Create action plan'}).click();
  await page.getByRole('button', {name: /Product Designer/}).click();
  await expect(page.getByRole('heading', {name: 'Evidence exercise: Prototyping'})).toBeVisible();
  await expect(page.getByRole('heading', {name: 'Evidence exercise: SQL'})).toHaveCount(0);
  await expect(page).toHaveURL(/report=42/);
});
