import { redirect } from 'next/navigation';

export default function RootPage() {
  // Standalone app mode: Open the NexPath Workspace directly without any login screen
  redirect('/dashboard');
}
