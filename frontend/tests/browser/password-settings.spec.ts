import { test, expect } from '@playwright/test';

test('password settings validate confirmation and replace the session', async ({page}) => {
  const user = {id:1,email:'test@example.com',full_name:'Alex Morgan'};
  await page.addInitScript(() => localStorage.setItem('careermind_token', 'old-session'));
  await page.route('**/api/v1/auth/me', route => route.fulfill({json:user}));
  await page.route('**/api/v1/user/settings', route => route.fulfill({json:{target_job_role:'Architect',preferred_ai_model:'Configured model'}}));
  let changes = 0;
  await page.route('**/api/v1/auth/change-password', async route => {
    changes++;
    expect(route.request().headers().authorization).toBe('Bearer old-session');
    expect(route.request().postDataJSON()).toEqual({current_password:'Original-password-123!',new_password:'Replacement-password-456!'});
    await route.fulfill({json:{access_token:'new-session',user}});
  });
  await page.goto('/dashboard/settings');
  await page.getByLabel('Current password', {exact:true}).fill('Original-password-123!');
  await page.getByLabel('New password', {exact:true}).fill('Replacement-password-456!');
  await page.getByLabel('Confirm new password', {exact:true}).fill('Different-password-789!');
  await page.getByRole('button',{name:'Change password',exact:true}).click();
  await expect(page.getByRole('alert').filter({hasText:'The new passwords do not match.'})).toBeVisible();
  expect(changes).toBe(0);
  await page.getByLabel('Confirm new password', {exact:true}).fill('Replacement-password-456!');
  await page.getByRole('button',{name:'Change password',exact:true}).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('careermind_token'))).toBe('new-session');
  await expect(page.getByLabel('Current password',{exact:true})).toHaveValue('');
  await expect(page.getByText('Password changed. Previous login sessions can no longer access your account.')).toBeVisible();
  expect(changes).toBe(1);
});
