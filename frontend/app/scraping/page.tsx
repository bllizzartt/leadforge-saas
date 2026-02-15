'use client';

import React, { useState, useEffect } from 'react';
import Layout from '@/app/layout';
import api from '@/lib/api';
import { ScrapingJob, ScrapingStatus, LeadSource } from '@/types';

export default function ScrapingPage() {
  const [activeTab, setActiveTab] = useState<'linkedin' | 'google_maps'>('linkedin');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  
  // LinkedIn form
  const [linkedInForm, setLinkedInForm] = useState({
    industry: '',
    location: '',
    company_size: '',
    job_titles: '',
    keywords: '',
    limit: 50
  });
  
  // Google Maps form
  const [mapsForm, setMapsForm] = useState({
    query: '',
    location: '',
    radius_km: 10,
    limit: 50
  });

  const handleLinkedInScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const response = await api.scrapeLinkedIn({
        industry: linkedInForm.industry,
        location: linkedInForm.location,
        company_size: linkedInForm.company_size,
        job_titles: linkedInForm.job_titles ? linkedInForm.job_titles.split(',').map(t => t.trim()) : [],
        keywords: linkedInForm.keywords ? linkedInForm.keywords.split(',').map(k => k.trim()) : [],
        limit: linkedInForm.limit
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Scraping failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleMapsScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const response = await api.scrapeGoogleMaps({
        query: mapsForm.query,
        location: mapsForm.location,
        radius_km: mapsForm.radius_km,
        limit: mapsForm.limit
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Scraping failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lead Scraping</h1>
          <p className="text-gray-500 mt-1">Find and import leads from various sources</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('linkedin')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'linkedin'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.75s.784-1.75 1.75-1.75 1.75.79 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
                LinkedIn
              </button>
              <button
                onClick={() => setActiveTab('google_maps')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'google_maps'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                </svg>
                Google Maps
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'linkedin' && (
              <form onSubmit={handleLinkedInScrape} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                    <input
                      type="text"
                      value={linkedInForm.industry}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, industry: e.target.value })}
                      placeholder="e.g., Technology, Healthcare, Finance"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={linkedInForm.location}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, location: e.target.value })}
                      placeholder="e.g., San Francisco, New York"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Company Size</label>
                    <select
                      value={linkedInForm.company_size}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, company_size: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Any size</option>
                      <option value="1-10">1-10 employees</option>
                      <option value="11-50">11-50 employees</option>
                      <option value="51-200">51-200 employees</option>
                      <option value="201-500">201-500 employees</option>
                      <option value="501-1000">501-1000 employees</option>
                      <option value="1001-5000">1001-5000 employees</option>
                      <option value="5001+">5001+ employees</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Job Titles</label>
                    <input
                      type="text"
                      value={linkedInForm.job_titles}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, job_titles: e.target.value })}
                      placeholder="VP of Engineering, CTO, Founder (comma separated)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
                    <input
                      type="text"
                      value={linkedInForm.keywords}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, keywords: e.target.value })}
                      placeholder="SaaS, AI, B2B (comma separated)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Results</label>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      value={linkedInForm.limit}
                      onChange={(e) => setLinkedInForm({ ...linkedInForm, limit: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Tips for LinkedIn Scraping</h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Be specific with job titles for better results</li>
                    <li>• Combine multiple filters for targeted leads</li>
                    <li>• Start with smaller limits to test your filters</li>
                  </ul>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Scraping LinkedIn...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      Start LinkedIn Scraping
                    </>
                  )}
                </button>
              </form>
            )}

            {activeTab === 'google_maps' && (
              <form onSubmit={handleGoogleMapsScrape} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Search Query</label>
                    <input
                      type="text"
                      required
                      value={mapsForm.query}
                      onChange={(e) => setMapsForm({ ...mapsForm, query: e.target.value })}
                      placeholder="e.g., restaurants, coffee shops, law firms"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={mapsForm.location}
                      onChange={(e) => setMapsForm({ ...mapsForm, location: e.target.value })}
                      placeholder="e.g., San Francisco, CA"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Radius (km)</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={mapsForm.radius_km}
                      onChange={(e) => setMapsForm({ ...mapsForm, radius_km: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Results</label>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      value={mapsForm.limit}
                      onChange={(e) => setMapsForm({ ...mapsForm, limit: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-green-900 mb-2">Google Maps Tips</h4>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• Search for local businesses in your target area</li>
                    <li>• Find contact info for small businesses</li>
                    <li>• Great for B2B local lead generation</li>
                  </ul>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Scraping Google Maps...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Start Google Maps Scraping
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <svg className="w-6 h-6 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-medium text-green-900">Scraping Complete!</h3>
            </div>
            <p className="text-green-700 mb-4">{result.message}</p>
            <div className="flex items-center space-x-4">
              <div className="bg-white rounded-lg px-4 py-2">
                <p className="text-2xl font-bold text-green-600">{result.leads_found}</p>
                <p className="text-sm text-green-600">Leads Found</p>
              </div>
              <a
                href="/leads"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                View Leads
              </a>
            </div>
          </div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Fast & Efficient</h3>
            <p className="text-gray-500 text-sm">Find hundreds of leads in minutes with our intelligent scraping engine.</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Verified Data</h3>
            <p className="text-gray-500 text-sm">Get enriched profiles with email verification and company data.</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Multiple Sources</h3>
            <p className="text-gray-500 text-sm">Scrape from LinkedIn, Google Maps, and more sources.</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
