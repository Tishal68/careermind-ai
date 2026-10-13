import { redirect } from 'next/navigation';

export default function RootPage() {
  // The dashboard restores authentication or redirects to sign in.
  redirect('/dashboard');
}
