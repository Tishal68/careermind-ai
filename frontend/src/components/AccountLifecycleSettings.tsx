"use client";

import { useState } from 'react';
import { Download, Trash2, ShieldAlert, CheckCircle, Mail, AlertTriangle } from 'lucide-react';
import { Card, Button, Input } from '@/components/UIComponents';
import { useAuth } from '@/context/AuthContext';
import { fetchApi } from '@/lib/api';

export default function AccountLifecycleSettings() {
  const { user, logout } = useAuth();
  
  // Export state
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState('');
  const [exportSuccess, setExportSuccess] = useState(false);

  // Verification state
  const [sendingVerification, setSendingVerification] = useState(false);
  const [verificationMsg, setVerificationMsg] = useState('');
  const [verificationError, setVerificationError] = useState('');

  // Delete state
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  async function handleExport() {
    setExporting(true);
    setExportError('');
    setExportSuccess(false);
    try {
      const data = await fetchApi<any>('/auth/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `careermind-export-${user?.id || 'account'}-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportSuccess(true);
    } catch (err: any) {
      setExportError(err.message || 'Could not export account data. Please try again.');
    } finally {
      setExporting(false);
    }
  }

  async function handleSendVerification() {
    setSendingVerification(true);
    setVerificationMsg('');
    setVerificationError('');
    try {
      const res = await fetchApi<any>('/auth/send-verification', { method: 'POST' });
      if (res.email_delivery_configured === false) {
        setVerificationMsg('Verification token generated. (Note: Email delivery service is not configured on this host).');
      } else {
        setVerificationMsg('Verification email sent! Check your inbox for the confirmation link.');
      }
    } catch (err: any) {
      setVerificationError(err.message || 'Could not send verification email. Please try again.');
    } finally {
      setSendingVerification(false);
    }
  }

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    setDeleteError('');
    if (deleteConfirmation !== 'DELETE MY ACCOUNT') {
      setDeleteError('Type the exact phrase "DELETE MY ACCOUNT" to confirm.');
      return;
    }
    if (!deletePassword) {
      setDeleteError('Enter your password to authorize account deletion.');
      return;
    }
    setDeleting(true);
    try {
      await fetchApi<any>('/auth/delete', {
        method: 'DELETE',
        body: JSON.stringify({
          password: deletePassword,
          confirmation: deleteConfirmation,
        }),
      });
      logout();
      window.location.href = '/register';
    } catch (err: any) {
      setDeleteError(err.message || 'Could not delete your account. Verify your password and try again.');
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Account Verification & Privacy */}
      <Card className="space-y-4 bg-[#0b1320] border-white/10 p-6">
        <div>
          <h2 className="flex items-center gap-2 font-semibold text-white text-sm">
            <Mail size={16} className="text-emerald-400" /> Account Status & Verification
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            View your email verification status and export your account data.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="space-y-0.5">
            <p className="text-xs text-slate-400">Email Address</p>
            <p className="text-sm font-semibold text-white">{user?.email}</p>
          </div>
          <div className="flex items-center gap-2">
            {user?.is_verified ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                <CheckCircle size={12} /> Verified
              </span>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={handleSendVerification}
                isLoading={sendingVerification}
                disabled={sendingVerification}
              >
                Send verification link
              </Button>
            )}
          </div>
        </div>

        {verificationMsg && (
          <p role="status" className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
            {verificationMsg}
          </p>
        )}
        {verificationError && (
          <p role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
            {verificationError}
          </p>
        )}

        <div className="pt-2 border-t border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-white">Data Portability (GDPR & CCPA)</p>
            <p className="text-xs text-slate-400">Download a full JSON archive of your resumes, career reports, and interview history.</p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleExport}
            isLoading={exporting}
            disabled={exporting}
            leftIcon={<Download size={14} />}
          >
            {exporting ? 'Exporting…' : 'Export Data'}
          </Button>
        </div>

        {exportSuccess && (
          <p role="status" className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
            Account data exported successfully. Check your browser downloads.
          </p>
        )}
        {exportError && (
          <p role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
            {exportError}
          </p>
        )}
      </Card>

      {/* Danger Zone: Account Deletion */}
      <Card className="space-y-4 bg-rose-950/20 border-rose-900/30 p-6">
        <div>
          <h2 className="flex items-center gap-2 font-semibold text-rose-300 text-sm">
            <AlertTriangle size={16} className="text-rose-400" /> Danger Zone: Delete Account
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Permanently delete your account, uploaded resumes, analysis reports, and interview sessions. This action is irreversible.
          </p>
        </div>

        {deleteError && (
          <p role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
            {deleteError}
          </p>
        )}

        <form onSubmit={handleDelete} className="space-y-3">
          <Input
            label="Current Password"
            type="password"
            autoComplete="current-password"
            value={deletePassword}
            onChange={e => setDeletePassword(e.target.value)}
            placeholder="Enter your current password"
            required
          />
          <div>
            <label htmlFor="confirm-delete-input" className="block text-xs font-semibold text-slate-300 mb-1.5">
              Type <span className="font-mono text-rose-400 font-bold">DELETE MY ACCOUNT</span> to confirm
            </label>
            <input
              id="confirm-delete-input"
              type="text"
              value={deleteConfirmation}
              onChange={e => setDeleteConfirmation(e.target.value)}
              placeholder="DELETE MY ACCOUNT"
              className="w-full rounded-xl bg-slate-900 border border-rose-900/40 p-3 text-sm text-white focus:outline-none focus:border-rose-500"
              required
            />
          </div>
          <Button
            type="submit"
            variant="danger"
            isLoading={deleting}
            disabled={deleting || deleteConfirmation !== 'DELETE MY ACCOUNT' || !deletePassword}
            leftIcon={<Trash2 size={14} />}
          >
            {deleting ? 'Deleting account…' : 'Permanently Delete Account'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
