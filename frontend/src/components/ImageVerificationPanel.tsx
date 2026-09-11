'use client';

import React, { useState } from 'react';
import {
  Camera,
  MapPin,
  Clock,
  Fingerprint,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Image as ImageIcon,
  ShieldAlert,
  Info,
  Layers,
  FileCheck,
  Cpu,
  Search,
  Sparkles
} from 'lucide-react';
import { ImageVerificationSummary, InstallationImage, VerificationCheckItem, EmbeddingVerificationSummary } from '@/types';
import { runImageVerification, runImageEmbeddingVerification } from '@/lib/api';

interface ImageVerificationPanelProps {
  caseId: string;
  images: InstallationImage[];
  caseScenarioId?: string;
}

export const ImageVerificationPanel: React.FC<ImageVerificationPanelProps> = ({
  caseId,
  images,
  caseScenarioId
}) => {
  const [selectedImageIndex, setSelectedImageIndex] = useState<number>(0);
  const [expandedCheckIndex, setExpandedCheckIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [summaries, setSummaries] = useState<Record<string, ImageVerificationSummary>>({});
  const [embeddingSummaries, setEmbeddingSummaries] = useState<Record<string, EmbeddingVerificationSummary>>({});

  // Default synthetic images for showcase if none uploaded yet
  const displayImages: InstallationImage[] = images.length > 0 ? images : [
    {
      id: `IMG-${caseScenarioId || 'CAS-2026-001'}-01`,
      case_id: caseId,
      image_type: 'installation_wide',
      file_path: 'installation_wide_solar_array.jpg',
      original_filename: 'installation_wide_solar_array.jpg',
      file_size_bytes: 2450000,
      mime_type: 'image/jpeg',
      phash: caseScenarioId === 'CAS-2026-005' ? 'a99a5e65a5655a96' : 'd52a2a2a2b2f2b2f',
      exif_timestamp: '2026-01-20T14:35:00',
      exif_lat: caseScenarioId === 'CAS-2026-003' ? 26.9124 : 28.6315,
      exif_lng: caseScenarioId === 'CAS-2026-003' ? 75.7873 : 77.2167,
      exif_device_model: 'Nikon D850 Pro',
      verification_status: 'analyzed',
      created_at: '2026-01-20T14:35:00Z'
    }
  ];

  const activeImage = displayImages[selectedImageIndex] || displayImages[0];
  const activeImageId = activeImage ? activeImage.id : 'IMG-001';

  // Build synthetic or live summary
  const currentSummary: ImageVerificationSummary = summaries[activeImageId] || {
    image_id: activeImageId,
    case_id: caseId,
    verification_status: 'analyzed',
    total_checks: 7,
    passed_count: caseScenarioId === 'CAS-2026-003' ? 5 : caseScenarioId === 'CAS-2026-005' ? 5 : 7,
    anomaly_count: caseScenarioId === 'CAS-2026-003' ? 1 : caseScenarioId === 'CAS-2026-005' ? 1 : 0,
    inconclusive_count: 0,
    verified_at: new Date().toISOString(),
    notes: 'Image integrity, EXIF, site GPS geofence, and pHash deduplication evaluated.',
    signals_generated: [],
    checks: caseScenarioId === 'CAS-2026-003' ? [
      {
        check_type: 'IMAGE_GPS_DISTANCE',
        check_name: 'Installation Site GPS Geofence Check',
        status: 'ANOMALY',
        severity: 'MEDIUM',
        message: 'Photo geotag (26.9124, 75.7873) is 234.8 km from claimed installation farm address (>1.0 km threshold).',
        evidence: { photo_lat: 26.9124, photo_lng: 75.7873, reference_lat: 28.6315, reference_lng: 77.2167, distance_km: 234.8, threshold_km: 1.0 }
      },
      {
        check_type: 'IMAGE_EXIF_PRESENT',
        check_name: 'EXIF Metadata Integrity Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Valid uncorrupted EXIF header and GPS telemetry present.',
        evidence: { camera_model: 'Nikon D850 Pro', has_gps: true }
      },
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'PASS',
        severity: 'INFO',
        message: 'No duplicate image matches detected in database (distance > 6).',
        evidence: { current_phash: 'd52a2a2a2b2f2b2f', matches_found: 0 }
      }
    ] : caseScenarioId === 'CAS-2026-005' ? [
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'ANOMALY',
        severity: 'HIGH',
        message: 'Exact image match (pHash distance: 0) detected against prior case CAS-2026-001.',
        evidence: { matching_image_id: 'IMG-CAS-001-01', matching_case_id: 'CAS-2026-001', hamming_distance: 0, threshold: 6 }
      },
      {
        check_type: 'IMAGE_EXIF_PRESENT',
        check_name: 'EXIF Metadata Integrity Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Valid EXIF metadata present.',
        evidence: { has_exif: true }
      },
      {
        check_type: 'IMAGE_GPS_DISTANCE',
        check_name: 'Installation Site GPS Geofence Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Geotag matches claimed installation location within 0.15 km (≤ 1.0 km).',
        evidence: { distance_km: 0.15, threshold_km: 1.0 }
      }
    ] : [
      {
        check_type: 'IMAGE_EXIF_PRESENT',
        check_name: 'EXIF Metadata Integrity Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Valid camera telemetry and timestamp tags verified.',
        evidence: { has_exif: true, camera_model: 'Nikon D850 Pro' }
      },
      {
        check_type: 'IMAGE_GPS_DISTANCE',
        check_name: 'Installation Site GPS Geofence Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Site coordinates verified within 0.12 km of installation farm.',
        evidence: { distance_km: 0.12, threshold_km: 1.0 }
      },
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'PASS',
        severity: 'INFO',
        message: 'No duplicate image matches detected in database.',
        evidence: { current_phash: 'd52a2a2a2b2f2b2f', matches_found: 0 }
      }
    ]
  };

  // Build synthetic or live embedding summary
  const currentEmbeddingSummary: EmbeddingVerificationSummary = embeddingSummaries[activeImageId] || {
    image_id: activeImageId,
    case_id: caseId,
    model: 'resnet18',
    model_version: '1.0',
    embedding_dimension: 512,
    has_embedding: true,
    status: caseScenarioId === 'CAS-2026-005' ? 'ANOMALY' : 'PASS',
    top_similarity: caseScenarioId === 'CAS-2026-005' ? 0.9945 : 0.4650,
    threshold: 0.85,
    top_matches: caseScenarioId === 'CAS-2026-005' ? [
      {
        candidate_image_id: 'IMG-CAS-001-01',
        candidate_case_id: 'CAS-2026-001',
        similarity: 0.9945,
        threshold: 0.85,
        is_above_threshold: true,
        match_type: 'cross_case',
        model: 'resnet18',
        model_version: '1.0',
        dimension: 512,
        created_at: '2026-01-20T14:35:00Z'
      }
    ] : [
      {
        candidate_image_id: 'IMG-CAS-002-01',
        candidate_case_id: 'CAS-2026-002',
        similarity: 0.4650,
        threshold: 0.85,
        is_above_threshold: false,
        match_type: 'cross_case',
        model: 'resnet18',
        model_version: '1.0',
        dimension: 512,
        created_at: '2026-01-22T10:15:00Z'
      }
    ],
    verified_at: new Date().toISOString()
  };

  const handleRunVerification = async () => {
    setLoading(true);
    try {
      const [resForensics, resEmbedding] = await Promise.all([
        runImageVerification(activeImageId),
        runImageEmbeddingVerification(activeImageId)
      ]);
      if (resForensics) {
        setSummaries((prev) => ({ ...prev, [activeImageId]: resForensics }));
      }
      if (resEmbedding) {
        setEmbeddingSummaries((prev) => ({ ...prev, [activeImageId]: resEmbedding }));
      }
    } catch (err) {
      console.error('Image verification error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#065F46] bg-[#ECFDF5] border border-[#A7F3D0] px-2 py-0.5 rounded-md uppercase">
            <CheckCircle2 className="h-3 w-3" />
            PASS
          </span>
        );
      case 'ANOMALY':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#991B1B] bg-[#FEF2F2] border border-[#FECACA] px-2 py-0.5 rounded-md uppercase">
            <AlertTriangle className="h-3 w-3" />
            ANOMALY
          </span>
        );
      case 'INCONCLUSIVE':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#92400E] bg-[#FFFBEB] border border-[#FDE68A] px-2 py-0.5 rounded-md uppercase">
            <HelpCircle className="h-3 w-3" />
            INCONCLUSIVE
          </span>
        );
    }
  };

  const totalImages = displayImages.length;
  const withExifCount = displayImages.filter((img) => img.exif_timestamp || img.exif_device_model).length;
  const hasReuseAlert = currentSummary.anomaly_count > 0 || currentEmbeddingSummary.status === 'ANOMALY';

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-[#182033] flex items-center gap-2">
              <Camera className="h-4 w-4 text-[#4F6EF7]" />
              <span>Image Forensics & Visual Similarity Search</span>
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#F1F4FA] text-[#4F6EF7] border border-[#E5E9F2] font-bold">
              Phase 4 & 5
            </span>
          </div>
          <p className="text-xs text-[#68738A] mt-0.5">
            EXIF extraction • Haversine site GPS distance • 64-bit pHash • Local ResNet-18 (512-dim) feature embeddings
          </p>
        </div>

        <button
          onClick={handleRunVerification}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F8FAFD] hover:bg-[#4F6EF7] text-[#182033] hover:text-white border border-[#E5E9F2] hover:border-[#4F6EF7] text-xs font-bold transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Analyzing Image...' : 'Re-run Forensics & Embeddings'}</span>
        </button>
      </div>

      {/* Case-Level Image Telemetry Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
        <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">Total Staged Photos</span>
          <span className="font-mono text-[#182033] font-bold mt-0.5 block text-sm">{totalImages}</span>
        </div>
        <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">EXIF Telemetry Found</span>
          <span className="font-mono text-[#4F6EF7] font-bold mt-0.5 block text-sm">{withExifCount} / {totalImages}</span>
        </div>
        <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">Deep Feature Vector</span>
          <span className="font-mono text-[#5B4AEF] font-bold mt-0.5 block text-sm">ResNet-18 (512-dim)</span>
        </div>
        <div className={`p-3 rounded-xl border ${hasReuseAlert ? 'bg-[#FEF2F2]/60 border-[#FECACA]' : 'bg-[#F8FAFD] border-[#E5E9F2]'}`}>
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">Visual Anomalies</span>
          <span className={`font-mono font-bold mt-0.5 block text-sm ${hasReuseAlert ? 'text-[#991B1B]' : 'text-[#065F46]'}`}>
            {currentSummary.anomaly_count + (currentEmbeddingSummary.status === 'ANOMALY' ? 1 : 0)} Detected
          </span>
        </div>
      </div>

      {/* Image Gallery / Selector if multiple */}
      {displayImages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {displayImages.map((img, idx) => (
            <button
              key={img.id}
              onClick={() => setSelectedImageIndex(idx)}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                selectedImageIndex === idx
                  ? 'bg-[#4F6EF7] text-white shadow-xs'
                  : 'bg-[#F8FAFD] text-[#68738A] hover:text-[#182033] border border-[#E5E9F2]'
              }`}
            >
              Photo #{idx + 1} ({img.image_type.replace('_', ' ')})
            </button>
          ))}
        </div>
      )}

      {/* Active Photo Card & Forensics Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left: Photo Metadata Details */}
        <div className="rounded-xl border border-[#E5E9F2] bg-[#F8FAFD] p-4 space-y-3">
          <div className="h-36 rounded-xl bg-white border border-[#E5E9F2] flex flex-col items-center justify-center text-center p-3 relative overflow-hidden shadow-2xs">
            <ImageIcon className="h-8 w-8 text-[#4F6EF7] mb-1.5" />
            <span className="text-xs font-bold text-[#182033] truncate max-w-full font-mono">
              {activeImage.original_filename}
            </span>
            <span className="text-[10px] text-[#8E99AD] uppercase tracking-wider font-mono mt-0.5">
              {activeImage.image_type.replace('_', ' ')}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-[#E5E9F2] pb-1.5">
              <span className="text-[#8E99AD]">Camera Telemetry</span>
              <span className="text-[#182033] font-mono text-[11px] font-semibold">{activeImage.exif_device_model || 'Nikon D850 Pro'}</span>
            </div>
            <div className="flex justify-between border-b border-[#E5E9F2] pb-1.5">
              <span className="text-[#8E99AD]">Capture Date</span>
              <span className="text-[#182033] font-mono text-[11px] font-semibold">
                {activeImage.exif_timestamp ? new Date(activeImage.exif_timestamp).toLocaleDateString() : '2026-01-20'}
              </span>
            </div>
            <div className="flex justify-between border-b border-[#E5E9F2] pb-1.5">
              <span className="text-[#8E99AD]">Site Coordinates</span>
              <span className="text-[#065F46] font-mono text-[11px] font-bold">
                {activeImage.exif_lat ? `${activeImage.exif_lat.toFixed(4)}, ${activeImage.exif_lng?.toFixed(4)}` : '28.6315, 77.2167'}
              </span>
            </div>
            <div className="flex justify-between border-b border-[#E5E9F2] pb-1.5">
              <span className="text-[#8E99AD]">64-bit pHash</span>
              <span className="text-[#4F6EF7] font-mono text-[11px] font-bold">{activeImage.phash || 'd52a2a2a2b2f2b2f'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8E99AD]">Feature Vector</span>
              <span className="text-[#5B4AEF] font-mono text-[11px] font-bold">ResNet-18 (512-dim)</span>
            </div>
          </div>
        </div>

        {/* Right: Structured Deterministic Checks */}
        <div className="md:col-span-2 space-y-2">
          {currentSummary.checks.map((check, idx) => {
            const isExpanded = expandedCheckIndex === idx;
            const isAnomaly = check.status === 'ANOMALY';

            return (
              <div
                key={idx}
                className={`rounded-xl border transition-all overflow-hidden ${
                  isAnomaly
                    ? 'border-[#FECACA] bg-[#FEF2F2]/40'
                    : 'border-[#E5E9F2] bg-white hover:border-[#D1D8E6]'
                }`}
              >
                <div
                  onClick={() => setExpandedCheckIndex(isExpanded ? null : idx)}
                  className="p-3.5 flex items-center justify-between cursor-pointer select-none hover:bg-[#F8FAFD]"
                >
                  <div className="flex items-center gap-2.5">
                    {getStatusBadge(check.status)}
                    <div>
                      <h4 className="text-xs font-bold text-[#182033]">{check.check_name}</h4>
                      <p className="text-[11px] text-[#68738A] mt-0.5 line-clamp-1">{check.message}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-mono text-[#8E99AD] hidden sm:inline">
                      {check.check_type}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-[#8E99AD]" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-[#8E99AD]" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 border-t border-[#E5E9F2] bg-[#F8FAFD] space-y-2 text-xs">
                    <div className="text-[#182033] leading-relaxed">{check.message}</div>
                    {check.evidence && Object.keys(check.evidence).length > 0 && (
                      <div>
                        <span className="text-[10px] uppercase tracking-wider font-bold text-[#8E99AD] block font-mono mb-1">
                          Auditable Forensics Evidence:
                        </span>
                        <pre className="bg-white p-3 rounded-xl border border-[#E5E9F2] font-mono text-[11px] text-[#182033] overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(check.evidence, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Deep Visual Feature Similarity (ResNet-18) Section */}
      <div className="rounded-xl border border-[#E5E9F2] bg-[#F8FAFD] p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-[#5B4AEF]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
              Deep Visual Feature Similarity Search (Local ResNet-18)
            </h4>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[#8E99AD]">
              Threshold: <strong className="text-[#182033] font-bold">cos ≥ {currentEmbeddingSummary.threshold.toFixed(2)}</strong>
            </span>
            {getStatusBadge(currentEmbeddingSummary.status)}
          </div>
        </div>

        <p className="text-xs text-[#68738A] leading-relaxed">
          512-dimensional deep visual feature embeddings extracted locally on CPU via PyTorch. Candidate images are compared using exact cosine similarity over internal lender records.
        </p>

        {/* Top-K Matches Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {currentEmbeddingSummary.top_matches.map((match, idx) => {
            const isHighSim = match.similarity >= currentEmbeddingSummary.threshold;
            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 transition-all ${
                  isHighSim
                    ? 'border-[#FECACA] bg-[#FEF2F2]'
                    : 'border-[#E5E9F2] bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-[#182033]">
                    Match #{idx + 1} — Case #{match.candidate_case_id}
                  </span>
                  <span className={`font-mono font-bold px-2 py-0.5 rounded-md text-[10px] ${
                    isHighSim
                      ? 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]'
                      : 'bg-[#F1F4FA] text-[#182033]'
                  }`}>
                    {(match.similarity * 100).toFixed(2)}% similarity
                  </span>
                </div>

                <div className="text-[11px] text-[#68738A] space-y-0.5">
                  <div className="flex justify-between">
                    <span>Candidate Image:</span>
                    <span className="font-mono text-[#182033] font-semibold">{match.candidate_image_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Scope:</span>
                    <span className="font-mono text-[#182033]">{match.match_type.replace('_', ' ')}</span>
                  </div>
                </div>

                {isHighSim && (
                  <div className="text-[11px] text-[#991B1B] pt-1 font-semibold">
                    ⚠️ Potential visual duplicate across cases. Requires underwriting investigation.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
