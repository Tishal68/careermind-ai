'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { ShieldCheck, Users, FileText, Target, BrainCircuit, Trash2, UserPlus, AlertCircle } from 'lucide-react';

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAdminData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const statsData = await fetchApi<any>('/admin/stats');
      const usersData = await fetchApi<any[]>('/admin/users');
      setStats(statsData);
      setUsersList(usersData);
    } catch (err: any) {
      setError(err.message || 'Failed to load Admin Special Access portal data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.is_superuser) {
      loadAdminData();
    }
  }, [user]);

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user account?')) return;
    try {
      await fetchApi(`/admin/users/${userId}`, { method: 'DELETE' });
      loadAdminData();
    } catch (err: any) {
      alert(err.message || 'Error deleting user.');
    }
  };

  const handleToggleAdmin = async (userId: number) => {
    try {
      await fetchApi(`/admin/users/${userId}/toggle-admin`, { method: 'POST' });
      loadAdminData();
    } catch (err: any) {
      alert(err.message || 'Error updating user admin status.');
    }
  };

  if (!user?.is_superuser) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center">
        <Card glass className="p-12 border-rose-500/30">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Access Denied</h1>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            You require <span className="text-purple-400 font-semibold">Special Superuser Admin Access</span> to view system administration controls.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-purple-400" />
          Special Admin System Control Center
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Superuser management dashboard for inspecting registered email accounts, system statistics, and user permissions.
        </p>
      </div>

      {/* Admin Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card glass className="p-4 text-center border-purple-500/30">
            <Users className="w-5 h-5 text-purple-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400 uppercase">Total Users</p>
            <p className="text-2xl font-extrabold text-white mt-1">{stats.total_users}</p>
          </Card>

          <Card glass className="p-4 text-center border-indigo-500/30">
            <FileText className="w-5 h-5 text-indigo-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400 uppercase">Parsed Resumes</p>
            <p className="text-2xl font-extrabold text-white mt-1">{stats.total_resumes}</p>
          </Card>

          <Card glass className="p-4 text-center border-pink-500/30">
            <Target className="w-5 h-5 text-pink-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400 uppercase">Career Reports</p>
            <p className="text-2xl font-extrabold text-white mt-1">{stats.total_reports}</p>
          </Card>

          <Card glass className="p-4 text-center border-emerald-500/30">
            <BrainCircuit className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400 uppercase">Mock Interviews</p>
            <p className="text-2xl font-extrabold text-white mt-1">{stats.total_interviews}</p>
          </Card>

          <Card glass className="p-4 text-center border-amber-500/30">
            <ShieldCheck className="w-5 h-5 text-amber-400 mx-auto mb-1" />
            <p className="text-xs text-slate-400 uppercase">Active Admins</p>
            <p className="text-2xl font-extrabold text-white mt-1">{stats.active_admins}</p>
          </Card>
        </div>
      )}

      {/* User Management Table */}
      <Card glass>
        <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Registered User Accounts ({usersList.length})
          </h2>
        </div>

        {error && <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs mb-4">{error}</div>}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/60 uppercase text-slate-400 border-b border-white/5">
              <tr>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Full Name</th>
                <th className="py-3 px-4">Email Address (Mail ID)</th>
                <th className="py-3 px-4">Role Badge</th>
                <th className="py-3 px-4">Registered Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {usersList.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40">
                  <td className="py-3.5 px-4 font-mono text-slate-400">#{u.id}</td>
                  <td className="py-3.5 px-4 font-semibold text-white">{u.full_name || 'Anonymous User'}</td>
                  <td className="py-3.5 px-4 text-indigo-300">{u.email}</td>
                  <td className="py-3.5 px-4">
                    {u.is_superuser ? (
                      <span className="px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 font-bold flex items-center gap-1 w-fit">
                        <ShieldCheck className="w-3 h-3" /> Special Admin
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 w-fit">
                        Standard User
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="py-3.5 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleToggleAdmin(u.id)}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                    >
                      {u.is_superuser ? 'Revoke Admin' : 'Grant Admin'}
                    </button>
                    {u.id !== user?.id && (
                      <button
                        onClick={() => handleDeleteUser(u.id)}
                        className="px-2 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
