'use client';

import React, { useState, useEffect } from 'react';
import Layout from '@/app/layout';
import api from '@/lib/api';
import { Campaign, CampaignDetail, CampaignStatus, EmailSequence } from '@/types';

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    has_more: false
  });
  const [showModal, setShowModal] = useState(false);
  const [showSequenceModal, setShowSequenceModal] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    from_name: '',
    from_email: '',
    throttling_emails_per_hour: 10,
    throttling_emails_per_day: 100
  });
  const [sequenceForm, setSequenceForm] = useState({
    step_order: 1,
    subject: '',
    body: '',
    delay_hours: 24
  });

  useEffect(() => {
    loadCampaigns();
  }, [pagination.page]);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const response = await api.getCampaigns({ page: pagination.page, page_size: pagination.page_size });
      setCampaigns(response.data.items);
      setPagination(prev => ({ ...prev, total: response.data.total, has_more: response.data.has_more }));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignDetail = async (id: number) => {
    try {
      const response = await api.getCampaign(id);
      setSelectedCampaign(response.data);
      setShowSequenceModal(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load campaign');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCampaign(formData);
      setShowModal(false);
      setFormData({ name: '', from_name: '', from_email: '', throttling_emails_per_hour: 10, throttling_emails_per_day: 100 });
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    }
  };

  const handleSequenceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCampaign) return;
    try {
      await api.addCampaignSequence(selectedCampaign.id, sequenceForm);
      setSequenceForm({ step_order: (selectedCampaign.sequences?.length || 0) + 1, subject: '', body: '', delay_hours: 24 });
      loadCampaignDetail(selectedCampaign.id);
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add sequence');
    }
  };

  const handleStart = async (id: number) => {
    try {
      await api.startCampaign(id);
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start campaign');
    }
  };

  const handlePause = async (id: number) => {
    try {
      await api.pauseCampaign(id);
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to pause campaign');
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm('Are you sure you want to cancel this campaign?')) return;
    try {
      await api.cancelCampaign(id);
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel campaign');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await api.deleteCampaign(id);
      loadCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete campaign');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-100 text-green-700';
      case 'paused': return 'bg-yellow-100 text-yellow-700';
      case 'completed': return 'bg-blue-100 text-blue-700';
      case 'canceled': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
            <p className="text-gray-500 mt-1">{pagination.total} total campaigns</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Campaign
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Campaigns Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns yet</h3>
            <p className="text-gray-500 mb-4">Create your first email campaign to start reaching leads</p>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Campaign
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{campaign.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Created {new Date(campaign.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(campaign.status)}`}>
                    {campaign.status}
                  </span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900">{campaign.total_leads}</p>
                    <p className="text-xs text-gray-500">Leads</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900">{campaign.emails_sent}</p>
                    <p className="text-xs text-gray-500">Sent</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900">{campaign.emails_opened}</p>
                    <p className="text-xs text-gray-500">Opens</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-gray-900">{campaign.emails_replied}</p>
                    <p className="text-xs text-gray-500">Replies</p>
                  </div>
                </div>

                {/* Performance */}
                <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                  <span>Open: {campaign.total_leads > 0 ? Math.round(campaign.emails_opened / campaign.total_leads * 100) : 0}%</span>
                  <span>Click: {campaign.total_leads > 0 ? Math.round(campaign.emails_clicked / campaign.total_leads * 100) : 0}%</span>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                  <div className="flex items-center space-x-2">
                    {campaign.status === 'draft' && (
                      <button
                        onClick={() => loadCampaignDetail(campaign.id)}
                        className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        Add Sequences
                      </button>
                    )}
                    {campaign.status === 'draft' && (
                      <button
                        onClick={() => handleStart(campaign.id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Start
                      </button>
                    )}
                    {campaign.status === 'running' && (
                      <button
                        onClick={() => handlePause(campaign.id)}
                        className="px-3 py-1 text-sm bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        Pause
                      </button>
                    )}
                    {campaign.status === 'paused' && (
                      <button
                        onClick={() => handleStart(campaign.id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Resume
                      </button>
                    )}
                    {(campaign.status === 'running' || campaign.status === 'paused') && (
                      <button
                        onClick={() => handleCancel(campaign.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(campaign.id)}
                    className="text-sm text-gray-500 hover:text-red-600 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.total > pagination.page_size && (
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {(pagination.page - 1) * pagination.page_size + 1} to {Math.min(pagination.page * pagination.page_size, pagination.total)} of {pagination.total} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={!pagination.has_more}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Campaign Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowModal(false)} />
            <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Create New Campaign</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From Name</label>
                  <input
                    type="text"
                    value={formData.from_name}
                    onChange={(e) => setFormData({ ...formData, from_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From Email</label>
                  <input
                    type="email"
                    value={formData.from_email}
                    onChange={(e) => setFormData({ ...formData, from_email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Emails/Hour</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.throttling_emails_per_hour}
                      onChange={(e) => setFormData({ ...formData, throttling_emails_per_hour: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Emails/Day</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.throttling_emails_per_day}
                      onChange={(e) => setFormData({ ...formData, throttling_emails_per_day: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-end space-x-3 pt-4">
                  <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg">Cancel</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Create Campaign</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Add Sequence Modal */}
      {showSequenceModal && selectedCampaign && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowSequenceModal(false)} />
            <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Email Sequences</h2>
              <p className="text-gray-500 mb-6">{selectedCampaign.name}</p>

              {/* Existing Sequences */}
              {selectedCampaign.sequences && selectedCampaign.sequences.length > 0 && (
                <div className="space-y-3 mb-6">
                  <h3 className="text-sm font-medium text-gray-700">Current Sequences</h3>
                  {selectedCampaign.sequences.map((seq: EmailSequence, idx: number) => (
                    <div key={seq.id} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Step {idx + 1}</span>
                        <span className="text-xs text-gray-500">{seq.delay_hours}h delay</span>
                      </div>
                      <p className="text-sm text-gray-900 mt-1">{seq.subject}</p>
                      <p className="text-xs text-gray-500 mt-1">{seq.emails_sent} sent • {seq.emails_opened} opens</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Add New Sequence */}
              <form onSubmit={handleSequenceSubmit} className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700">Add Email Step</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line</label>
                  <input
                    type="text"
                    required
                    value={sequenceForm.subject}
                    onChange={(e) => setSequenceForm({ ...sequenceForm, subject: e.target.value })}
                    placeholder="Hi {{first_name}}, quick question about {{company}}"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Body</label>
                  <textarea
                    required
                    rows={6}
                    value={sequenceForm.body}
                    onChange={(e) => setSequenceForm({ ...sequenceForm, body: e.target.value })}
                    placeholder="Hi {{first_name}},&#10;&#10;I noticed that {{company}} might be interested in...&#10;&#10;Best,&#10;{{my_name}}"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Available tokens: {'{{first_name}}'}, {'{{company}}'}, {'{{title}}'}, {'{{my_name}}'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Delay (hours)</label>
                  <input
                    type="number"
                    min="1"
                    value={sequenceForm.delay_hours}
                    onChange={(e) => setSequenceForm({ ...sequenceForm, delay_hours: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center justify-end space-x-3 pt-4">
                  <button type="button" onClick={() => setShowSequenceModal(false)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg">Done</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Add Step</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
