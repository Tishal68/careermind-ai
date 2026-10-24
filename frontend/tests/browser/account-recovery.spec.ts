import { test, expect } from '@playwright/test';

test('password recovery is reachable and displays unavailable email honestly', async ({page}) => {
  await page.route('**/api/v1/auth/forgot-password', route => route.fulfill({status:503,json:{detail:'Password recovery email is unavailable. Please contact support or try again later.'}}));
  await page.goto('/login');
  await page.getByRole('link', {name:'Forgot password?'}).click();
  await expect(page.getByRole('heading', {name:'Recover your account'})).toBeVisible();
  await page.getByLabel('Email address').fill('test@example.com');
  await page.getByRole('button', {name:'Send reset link'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('email is unavailable');
  await expect(page.getByLabel('Email address')).toHaveValue('test@example.com');
});

test('reset link keeps its token out of the URL and validates confirmation', async ({page}) => {
  let requests = 0;
  await page.route('**/api/v1/auth/reset-password', route => {
    requests++;
    expect(route.request().postDataJSON()).toEqual({token:'test-reset-token',new_password:'Replacement-password-456!'});
    return route.fulfill({json:{detail:'Password has been reset successfully. Please sign in with your new password.'}});
  });
  await page.goto('/reset-password#token=test-reset-token');
  await expect(page).toHaveURL(/\/reset-password$/);
  await page.getByLabel('New password', {exact:true}).fill('Replacement-password-456!');
  await page.getByLabel('Confirm new password').fill('Mismatch-password-123!');
  await page.getByRole('button', {name:'Reset password'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('do not match');
  expect(requests).toBe(0);
  await page.getByLabel('Confirm new password').fill('Replacement-password-456!');
  await page.getByRole('button', {name:'Reset password'}).click();
  await expect(page.getByRole('status')).toContainText('reset successfully');
  expect(requests).toBe(1);
});

test('verification requires deliberate confirmation and reports expired links', async ({page}) => {
  let requests = 0;
  await page.route('**/api/v1/auth/verify-email', route => {
    requests++;
    return route.fulfill({status:400,json:{detail:'Invalid or expired verification token.'}});
  });
  await page.goto('/verify-email#token=expired-token');
  await expect(page.getByRole('heading', {name:'Verify your email'})).toBeVisible();
  expect(requests).toBe(0);
  await page.getByRole('button', {name:'Verify email', exact:true}).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('expired');
});
