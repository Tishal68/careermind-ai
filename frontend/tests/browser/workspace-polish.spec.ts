import { test, expect } from '@playwright/test';

async function workspace(page: import('@playwright/test').Page) {
  await page.addInitScript(() => localStorage.setItem('careermind_token', 'visual-test'));
  await page.route('**/api/v1/auth/me', route => route.fulfill({json:{id:1,email:'test@example.com',full_name:'Alex Morgan'}}));
  await page.route('**/api/v1/user/settings', route => route.fulfill({json:{target_job_role:'',preferred_ai_model:'Configured model'}}));
  await page.route('**/api/v1/resume/my-resumes', route => route.fulfill({json:[]}));
  await page.route('**/api/v1/analysis/reports?limit=1', route => route.fulfill({json:[]}));
}

for (const width of [390, 1440]) {
  test(`workspace navigation and layout at ${width}px`, async ({page}) => {
    await page.setViewportSize({width, height:1000});
    await workspace(page);
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', {name:'A clear path to your next role'})).toBeVisible();
    const nav = page.getByRole('navigation', {name:width < 1024 ? 'Mobile navigation' : 'Main navigation', exact:true});
    await expect(nav.getByRole('link', {name:'Role match', exact:true})).toHaveAttribute('aria-current','page');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({path:`test-results/workspace-${width}.png`,fullPage:true});
    await nav.getByRole('link', {name:'Settings', exact:true}).click();
    await expect(page).toHaveURL(/settings$/);
    await expect(nav.getByRole('link', {name:'Settings', exact:true})).toHaveAttribute('aria-current','page');
  });
}

test('slow saved resumes do not block role entry or keyboard navigation', async ({page}) => {
  await workspace(page);
  let release = () => {};
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/resume/my-resumes', async route => { await gate; await route.fulfill({json:[]}); });
  await page.goto('/dashboard');
  await expect(page.getByText('Loading saved resumes…', {exact:false})).toBeVisible();
  await page.getByLabel('1. Choose your target role').fill('Landscape Architect');
  await expect(page.getByRole('button',{name:'Research my role match',exact:true})).toBeDisabled();
  release();
  await expect(page.getByRole('button',{name:'Research my role match',exact:true})).toBeEnabled();
  await expect(page.getByLabel('1. Choose your target role')).toHaveValue('Landscape Architect');
  await page.keyboard.press('Control+Home');
  await page.getByRole('link',{name:'Skip to content'}).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
});

test('login stays within mobile viewport with reduced motion', async ({page}) => {
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/login');
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/login-mobile.png',fullPage:true});
});
