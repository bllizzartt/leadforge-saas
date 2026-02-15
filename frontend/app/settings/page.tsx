'use client';

import React, { useState, useEffect } from 'react';
import Layout from '@/app/layout';
import api from '@/lib/api';
import { Company, PlanType } from '@/types';

export default function SettingsPage() {
  const [company, setCompany] = useState<Company | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [activeTab, setActiveTab] = useState('general');
  
  const [formData, setFormData] = useState({
    name: '',
    billing_email: '',
    logo_url: ''
  });
  
  const [emailSettings, setEmailSettings] = useState({
    default_from_name: '',
    default_from_email: '',
    reply_to_email: '',
    email_signature_html: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [companyRes, settingsRes] = await Promise.all([
        api.getCompany(),
        api.getCompanySettings()
      ]);
      setCompany(companyRes.data);
      setSettings(settingsRes.data);
      setFormData({
        name: companyRes.data.name,
        billing_email: companyRes.data.billing_email || '',
        logo_url: companyRes.data.logo_url || ''
      });
      setEmailSettings({
        default_from_name: settingsRes.data.default_from_name || '',
        default_from_email: settingsRes.data.default_from_email || '',
        reply_to_email: settingsRes.data.reply_to_email || '',
        email_signature_html: settingsRes.data.email_signature_html || ''
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleCompanySave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      await api.updateCompany(formData);
      setSuccess('Company settings saved successfully');
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleEmailSettingsSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      await api.updateCompanySettings(emailSettings);
      setSuccess('Email settings saved successfully');
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Manage your account and workspace settings</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {['general', 'email', 'integrations', 'billing'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors capitalize ${
                    activeTab === tab
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* General Settings */}
            {activeTab === 'general' && (
              <form onSubmit={handleCompanySave} className="space-y-6">
                {/* Plan Info */}
                <div className="bg-blue-50 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-900">Current Plan</p>
                      <p className="text-2xl font-bold text-blue-600 capitalize">{company?.plan}</p>
                    </div>
                    <button type="button" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                      Upgrade Plan
                    </button>
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-blue-700">Leads Limit</p>
                      <p className="font-medium text-blue-900">{company?.leads_limit || 0} leads</p>
                    </div>
                    <div>
                      <p className="text-blue-700">Users Limit</p>
                      <p className="font-medium text-blue-900">{company?.users_limit || 0} users</p>
                    </div>
                    <div>
                      <p className="text-blue-700">Emails/Month</p>
                      <p className="font-medium text-blue-900">{company?.emails_per_month || 0}</p>
                    </div>
                  </div>
                </div>

                {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}
                {success && <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">{success}</div>}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Billing Email</label>
                  <input
                    type="email"
                    value={formData.billing_email}
                    onChange={(e) => setFormData({ ...formData, billing_email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Logo URL</label>
                  <input
                    type="url"
                    value={formData.logo_url}
                    onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                    placeholder="https://your-domain.com/logo.png"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            )}

            {/* Email Settings */}
            {activeTab === 'email' && (
              <form onSubmit={handleEmailSettingsSave} className="space-y-6">
                <div className="bg-yellow-50 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <h4 className="text-sm font-medium text-yellow-900">Configure your email settings</h4>
                      <p className="text-sm text-yellow-700 mt-1">Set up your sending domain and DKIM records for better deliverability.</p>
                    </div>
                  </div>
                </div>

                {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>}
                {success && <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">{success}</div>}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Default From Name</label>
                  <input
                    type="text"
                    value={emailSettings.default_from_name}
                    onChange={(e) => setEmailSettings({ ...emailSettings, default_from_name: e.target.value })}
                    placeholder="Your Name or Company"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Default From Email</label>
                  <input
                    type="email"
                    value={emailSettings.default_from_email}
                    onChange={(e) => setEmailSettings({ ...emailSettings, default_from_email: e.target.value })}
                    placeholder="you@yourdomain.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reply-To Email</label>
                  <input
                    type="email"
                    value={emailSettings.reply_to_email}
                    onChange={(e) => setEmailSettings({ ...emailSettings, reply_to_email: e.target.value })}
                    placeholder="reply@yourdomain.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Signature (HTML)</label>
                  <textarea
                    rows={4}
                    value={emailSettings.email_signature_html}
                    onChange={(e) => setEmailSettings({ ...emailSettings, email_signature_html: e.target.value })}
                    placeholder="<p>Best regards,<br/>Your Name</p>"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Email Settings'}
                </button>
              </form>
            )}

            {/* Integrations */}
            {activeTab === 'integrations' && (
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Email Verification</h3>
                  <p className="text-gray-500 text-sm mb-4">Connect your email verification provider for accurate deliverability.</p>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                          <span className="text-lg font-bold text-orange-600">H</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Hunter.io</p>
                          <p className="text-sm text-gray-500">Email finder & verification</p>
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                        Connect
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <span className="text-lg font-bold text-blue-600">N</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">NeverBounce</p>
                          <p className="text-sm text-gray-500">Real-time email validation</p>
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                        Connect
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Data Enrichment</h3>
                  <p className="text-gray-500 text-sm mb-4">Enrich your leads with company and contact data.</p>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                          <span className="text-lg font-bold text-red-600">C</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Clearbit</p>
                          <p className="text-sm text-gray-500">Company & contact enrichment</p>
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                        Connect
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                          <span className="text-lg font-bold text-green-600">B</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">BuiltWith</p>
                          <p className="text-sm text-gray-500">Technology stack detection</p>
                        </div>
                      </div>
                      <button className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                        Connect
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Billing */}
            {activeTab === 'billing' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
                  <h3 className="text-xl font-bold mb-2">{company?.plan?.charAt(0).toUpperCase()}{company?.plan?.slice(1)} Plan</h3>
                  <p className="opacity-90">Your current subscription tier</p>
                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      <p className="text-3xl font-bold">${company?.plan === 'starter' ? '29' : company?.plan === 'growth' ? '99' : '299'}<span className="text-sm font-normal opacity-75">/month</span></p>
                    </div>
                    <button className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-colors">
                      Upgrade
                    </button>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Usage This Month</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">Leads</span>
                        <span className="text-sm font-medium">0 / {company?.leads_limit || 0}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: '0%' }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">Emails Sent</span>
                        <span className="text-sm font-medium">0 / {company?.emails_per_month || 0}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{ width: '0%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Method</h3>
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-6 bg-gray-300 rounded flex items-center justify-center text-xs font-bold text-gray-600">
                        CARD
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">No payment method</p>
                        <p className="text-sm text-gray-500">Add a card to start paid features</p>
                      </div>
                    </div>
                    <button className="text-sm text-blue-600 hover:text-blue-700">Add Card</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
