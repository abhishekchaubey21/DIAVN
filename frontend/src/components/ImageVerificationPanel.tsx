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
  const [showEmbeddingDetails, setShowEmbeddingDetails] = useState<boolean>(true);
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
      created_at: new Date().toISOString()
    }
  ];

  const activeImage = displayImages[selectedImageIndex] || displayImages[0];
  const activeImageId = activeImage.id;

  // Build synthetic deterministic image summary based on case scenario if API response not yet loaded
  const currentSummary: ImageVerificationSummary = summaries[activeImageId] || {
    image_id: activeImageId,
    case_id: caseId,
    original_filename: activeImage.original_filename,
    image_type: activeImage.image_type,
    verification_status: 'completed',
    total_checks: 7,
    passed_count: caseScenarioId === 'CAS-2026-003' || caseScenarioId === 'CAS-2026-005' ? 5 : 7,
    anomaly_count: caseScenarioId === 'CAS-2026-003' || caseScenarioId === 'CAS-2026-005' ? 1 : 0,
    inconclusive_count: 0,
    verified_at: new Date().toISOString(),
    notes: 'Deterministic installation image forensics completed. Final composite risk score not yet computed.',
    signals_generated: [],
    exif_summary: {
      has_exif: true,
      camera_make: 'Nikon',
      camera_model: 'D850 Pro',
      capture_timestamp: activeImage.exif_timestamp,
      gps_lat: activeImage.exif_lat,
      gps_lng: activeImage.exif_lng
    },
    phash: activeImage.phash,
    checks: caseScenarioId === 'CAS-2026-005' ? [
      {
        check_type: 'IMAGE_FILE_INTEGRITY',
        check_name: 'Image File Integrity & Container Validation',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image decoded successfully (JPEG, 3200x2400px, 2.45 MB).',
        evidence: { detected_format: 'JPEG', dimensions: [3200, 2400], file_size_bytes: 2450000 }
      },
      {
        check_type: 'EXIF_METADATA',
        check_name: 'EXIF Telemetry & Camera Metadata Presence',
        status: 'PASS',
        severity: 'INFO',
        message: 'EXIF metadata successfully extracted (Camera: Nikon D850 Pro, Captured: 2026-01-20T14:35:00).',
        evidence: { camera_make: 'Nikon', camera_model: 'D850 Pro', capture_timestamp: '2026-01-20T14:35:00', has_gps: true }
      },
      {
        check_type: 'GPS_COORDINATE_VALIDITY',
        check_name: 'Photo Geotag & Coordinate Boundary Validity',
        status: 'PASS',
        severity: 'INFO',
        message: 'GPS coordinates (28.6315, 77.2167) are valid within standard bounds.',
        evidence: { gps_lat: 28.6315, gps_lng: 77.2167 }
      },
      {
        check_type: 'GPS_LOCATION_CONSISTENCY',
        check_name: 'Installation Site GPS Distance Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Photo GPS is within 0.42 km of claimed installation site (allowed threshold: 1.0 km).',
        evidence: { photo_lat: 28.6315, photo_lng: 77.2167, reference_lat: 28.6290, reference_lng: 77.2220, distance_km: 0.42, threshold_km: 1.0 }
      },
      {
        check_type: 'IMAGE_TIMESTAMP_CONSISTENCY',
        check_name: 'Photo Capture Timestamp & Chronology Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Photo capture date is consistent with underwriting timeline (+5 days relative to invoice_date).',
        evidence: { photo_capture_date: '2026-01-20', reference_date: '2026-01-15', delta_days: 5 }
      },
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Internal Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'ANOMALY',
        severity: 'HIGH',
        message: "Exact perceptual match (Hamming distance 0) detected with installation image from case #CAS-2026-001. Requires underwriter review.",
        evidence: {
          current_image_id: activeImageId,
          current_case_id: caseId,
          current_phash: 'a99a5e65a5655a96',
          matching_case_id: 'CAS-2026-001',
          matching_image_id: 'IMG-CAS-001-01',
          hamming_distance: 0,
          threshold: 6,
          registry_scope: 'internal_lender_records'
        }
      },
      {
        check_type: 'IMAGE_SAME_CASE_DUPLICATE',
        check_name: 'Intra-Case Image Redundancy Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image is unique within current case.',
        evidence: { intra_case_duplicates: 0 }
      }
    ] : caseScenarioId === 'CAS-2026-003' ? [
      {
        check_type: 'IMAGE_FILE_INTEGRITY',
        check_name: 'Image File Integrity & Container Validation',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image decoded successfully (JPEG, 3200x2400px, 2.45 MB).',
        evidence: { detected_format: 'JPEG', dimensions: [3200, 2400], file_size_bytes: 2450000 }
      },
      {
        check_type: 'EXIF_METADATA',
        check_name: 'EXIF Telemetry & Camera Metadata Presence',
        status: 'PASS',
        severity: 'INFO',
        message: 'EXIF metadata successfully extracted (Camera: Nikon D850 Pro, Captured: 2026-01-20T14:35:00).',
        evidence: { camera_make: 'Nikon', camera_model: 'D850 Pro', capture_timestamp: '2026-01-20T14:35:00', has_gps: true }
      },
      {
        check_type: 'GPS_COORDINATE_VALIDITY',
        check_name: 'Photo Geotag & Coordinate Boundary Validity',
        status: 'PASS',
        severity: 'INFO',
        message: 'GPS coordinates (26.9124, 75.7873) are valid within standard bounds.',
        evidence: { gps_lat: 26.9124, gps_lng: 75.7873 }
      },
      {
        check_type: 'GPS_LOCATION_CONSISTENCY',
        check_name: 'Installation Site GPS Distance Consistency',
        status: 'ANOMALY',
        severity: 'HIGH',
        message: 'Photo GPS is 234.8 km away from claimed installation site (exceeds threshold of 1.0 km).',
        evidence: { photo_lat: 26.9124, photo_lng: 75.7873, reference_lat: 28.6290, reference_lng: 77.2220, distance_km: 234.8, threshold_km: 1.0 }
      },
      {
        check_type: 'IMAGE_TIMESTAMP_CONSISTENCY',
        check_name: 'Photo Capture Timestamp & Chronology Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Photo capture date is consistent with underwriting timeline (+5 days relative to invoice_date).',
        evidence: { photo_capture_date: '2026-01-20', reference_date: '2026-01-15', delta_days: 5 }
      },
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Internal Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'PASS',
        severity: 'INFO',
        message: 'No matching or near-duplicate installation images detected in internal database (threshold: d <= 6).',
        evidence: { current_phash: 'd52a2a2a2b2f2b2f', matches_found: 0, threshold: 6 }
      },
      {
        check_type: 'IMAGE_SAME_CASE_DUPLICATE',
        check_name: 'Intra-Case Image Redundancy Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image is unique within current case.',
        evidence: { intra_case_duplicates: 0 }
      }
    ] : [
      {
        check_type: 'IMAGE_FILE_INTEGRITY',
        check_name: 'Image File Integrity & Container Validation',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image decoded successfully (JPEG, 3200x2400px, 2.45 MB).',
        evidence: { detected_format: 'JPEG', dimensions: [3200, 2400], file_size_bytes: 2450000 }
      },
      {
        check_type: 'EXIF_METADATA',
        check_name: 'EXIF Telemetry & Camera Metadata Presence',
        status: 'PASS',
        severity: 'INFO',
        message: 'EXIF metadata successfully extracted (Camera: Nikon D850 Pro, Captured: 2026-01-20T14:35:00).',
        evidence: { camera_make: 'Nikon', camera_model: 'D850 Pro', capture_timestamp: '2026-01-20T14:35:00', has_gps: true }
      },
      {
        check_type: 'GPS_COORDINATE_VALIDITY',
        check_name: 'Photo Geotag & Coordinate Boundary Validity',
        status: 'PASS',
        severity: 'INFO',
        message: 'GPS coordinates (28.6315, 77.2167) are valid within standard bounds.',
        evidence: { gps_lat: 28.6315, gps_lng: 77.2167 }
      },
      {
        check_type: 'GPS_LOCATION_CONSISTENCY',
        check_name: 'Installation Site GPS Distance Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Photo GPS is within 0.42 km of claimed installation site (allowed threshold: 1.0 km).',
        evidence: { photo_lat: 28.6315, photo_lng: 77.2167, reference_lat: 28.6290, reference_lng: 77.2220, distance_km: 0.42, threshold_km: 1.0 }
      },
      {
        check_type: 'IMAGE_TIMESTAMP_CONSISTENCY',
        check_name: 'Photo Capture Timestamp & Chronology Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Photo capture date is consistent with underwriting timeline (+5 days relative to invoice_date).',
        evidence: { photo_capture_date: '2026-01-20', reference_date: '2026-01-15', delta_days: 5 }
      },
      {
        check_type: 'IMAGE_PHASH_REUSE',
        check_name: 'Internal Image Perceptual Hash (pHash) Cross-Case Reuse',
        status: 'PASS',
        severity: 'INFO',
        message: 'No matching or near-duplicate installation images detected in internal database (threshold: d <= 6).',
        evidence: { current_phash: 'd52a2a2a2b2f2b2f', matches_found: 0, threshold: 6 }
      },
      {
        check_type: 'IMAGE_SAME_CASE_DUPLICATE',
        check_name: 'Intra-Case Image Redundancy Check',
        status: 'PASS',
        severity: 'INFO',
        message: 'Image is unique within current case.',
        evidence: { intra_case_duplicates: 0 }
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
      },
      {
        candidate_image_id: 'IMG-CAS-002-01',
        candidate_case_id: 'CAS-2026-002',
        similarity: 0.5320,
        threshold: 0.85,
        is_above_threshold: false,
        match_type: 'cross_case',
        model: 'resnet18',
        model_version: '1.0',
        dimension: 512,
        created_at: '2026-01-22T10:15:00Z'
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
      console.error('Image verification execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/40 px-2 py-0.5 rounded">
            <CheckCircle2 className="h-3.5 w-3.5" />
            PASS
          </span>
        );
      case 'ANOMALY':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-rose-400 bg-rose-950/60 border border-rose-500/40 px-2 py-0.5 rounded animate-pulse">
            <AlertTriangle className="h-3.5 w-3.5" />
            ANOMALY
          </span>
        );
      case 'INCONCLUSIVE':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-slate-300 bg-slate-800 border border-slate-700 px-2 py-0.5 rounded">
            <HelpCircle className="h-3.5 w-3.5" />
            INCONCLUSIVE
          </span>
        );
    }
  };

  // Calculate Case-Level Image Metrics
  const totalImages = displayImages.length;
  const withExifCount = displayImages.filter((img) => img.exif_timestamp || img.exif_device_model).length;
  const withGpsCount = displayImages.filter((img) => img.exif_lat !== undefined && img.exif_lat !== null).length;
  const hasReuseAlert = currentSummary.anomaly_count > 0 || currentEmbeddingSummary.status === 'ANOMALY';

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 backdrop-blur-md space-y-5 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-indigo-400" />
            <h3 className="text-base font-bold text-slate-100">
              Installation Image Forensics & Deep Visual Feature Similarity
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            EXIF extraction • Haversine site GPS distance • 64-bit pHash • Local ResNet-18 (512-dim) feature embeddings
          </p>
        </div>

        <button
          onClick={handleRunVerification}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold shadow-md transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Analyzing Image...' : 'Re-run Forensics & Embeddings'}</span>
        </button>
      </div>

      {/* Case-Level Image Telemetry Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center text-xs">
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">Total Staged Photos</span>
          <span className="font-mono text-slate-200 font-bold mt-0.5 block text-sm">{totalImages}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">EXIF Telemetry Found</span>
          <span className="font-mono text-cyan-400 font-bold mt-0.5 block text-sm">{withExifCount} / {totalImages}</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">Deep Feature Vector</span>
          <span className="font-mono text-indigo-400 font-bold mt-0.5 block text-sm">ResNet-18 (512-dim)</span>
        </div>
        <div className={`p-2.5 rounded-lg border ${hasReuseAlert ? 'bg-rose-950/30 border-rose-500/40' : 'bg-slate-950/70 border-slate-800'}`}>
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">Visual Anomalies</span>
          <span className={`font-mono font-bold mt-0.5 block text-sm ${hasReuseAlert ? 'text-rose-400' : 'text-emerald-400'}`}>
            {currentSummary.anomaly_count + (currentEmbeddingSummary.status === 'ANOMALY' ? 1 : 0)} Anomalies Detected
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
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                selectedImageIndex === idx
                  ? 'bg-indigo-600 text-white shadow'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              Photo #{idx + 1} ({img.image_type.replace('_', ' ')})
            </button>
          ))}
        </div>
      )}

      {/* Active Photo Card & Forensics Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left: Simulated / Actual Photo Preview & Metadata */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 space-y-3">
          <div className="h-40 rounded-md bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800/80 flex flex-col items-center justify-center text-center p-3 relative overflow-hidden">
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:12px_12px]" />
            <ImageIcon className="h-9 w-9 text-indigo-400 mb-1.5" />
            <span className="text-xs font-semibold text-slate-200 truncate max-w-full font-mono">
              {activeImage.original_filename}
            </span>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono mt-0.5">
              {activeImage.image_type.replace('_', ' ')}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-slate-800 pb-1.5">
              <span className="text-slate-500">Camera Telemetry</span>
              <span className="text-slate-300 font-mono text-[11px]">{activeImage.exif_device_model || 'Nikon D850 Pro'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-1.5">
              <span className="text-slate-500">Capture Date</span>
              <span className="text-slate-300 font-mono text-[11px]">
                {activeImage.exif_timestamp ? new Date(activeImage.exif_timestamp).toLocaleDateString() : '2026-01-20'}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-1.5">
              <span className="text-slate-500">Site Coordinates</span>
              <span className="text-emerald-400 font-mono text-[11px]">
                {activeImage.exif_lat ? `${activeImage.exif_lat.toFixed(4)}, ${activeImage.exif_lng?.toFixed(4)}` : '28.6315, 77.2167'}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-1.5">
              <span className="text-slate-500">64-bit pHash</span>
              <span className="text-indigo-400 font-mono text-[11px]">{activeImage.phash || 'd52a2a2a2b2f2b2f'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Feature Vector</span>
              <span className="text-purple-400 font-mono text-[11px]">ResNet-18 (512-dim, L2)</span>
            </div>
          </div>
        </div>

        {/* Right: 7 Structured Deterministic Checks */}
        <div className="md:col-span-2 space-y-2">
          {currentSummary.checks.map((check, idx) => {
            const isExpanded = expandedCheckIndex === idx;
            const isAnomaly = check.status === 'ANOMALY';

            return (
              <div
                key={idx}
                className={`rounded-lg border transition-all ${
                  isAnomaly
                    ? 'border-rose-500/40 bg-rose-950/20'
                    : check.status === 'PASS'
                      ? 'border-slate-800 bg-slate-950/40'
                      : 'border-slate-800 bg-slate-950/30'
                }`}
              >
                <div
                  onClick={() => setExpandedCheckIndex(isExpanded ? null : idx)}
                  className="p-3 flex items-center justify-between cursor-pointer select-none"
                >
                  <div className="flex items-center gap-2.5">
                    {getStatusBadge(check.status)}
                    <div>
                      <h4 className="text-xs font-semibold text-slate-200">{check.check_name}</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{check.message}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-mono text-slate-500 hidden sm:inline">
                      {check.check_type}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expandable Evidence Payload */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 space-y-2 text-xs">
                    <div className="text-slate-300 font-normal">{check.message}</div>
                    {check.evidence && Object.keys(check.evidence).length > 0 && (
                      <div>
                        <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block font-mono mb-1">
                          Auditable Forensics Evidence Payload:
                        </span>
                        <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
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

      {/* Phase 5: Deep Visual Feature Similarity (ResNet-18) Section */}
      <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-purple-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Deep Visual Feature Similarity Search (Local ResNet-18)
            </h4>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400">
              Provisional Threshold: <strong className="text-slate-200 font-bold">cos ≥ {currentEmbeddingSummary.threshold.toFixed(2)}</strong>
            </span>
            {getStatusBadge(currentEmbeddingSummary.status)}
          </div>
        </div>

        <p className="text-xs text-slate-400">
          512-dimensional deep visual feature embeddings extracted locally on CPU via PyTorch. Candidate images are compared using exact cosine similarity over internal lender records.
        </p>

        {/* Top-K Matches Grid */}
        <div className="space-y-2 pt-1">
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block font-mono">
            Top-K Nearest Visual Matches in Internal Registry:
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {currentEmbeddingSummary.top_matches.map((match, idx) => {
              const isHighSim = match.similarity >= currentEmbeddingSummary.threshold;
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border text-xs space-y-1.5 transition-all ${
                    isHighSim
                      ? 'border-rose-500/40 bg-rose-950/20'
                      : 'border-slate-800 bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-slate-200">
                      Match #{idx + 1} — Case #{match.candidate_case_id}
                    </span>
                    <span className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                      isHighSim
                        ? 'bg-rose-950/80 text-rose-300 border border-rose-500/40'
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {(match.similarity * 100).toFixed(2)}% similarity
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 space-y-0.5">
                    <div className="flex justify-between">
                      <span>Candidate Image:</span>
                      <span className="font-mono text-slate-300">{match.candidate_image_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Scope:</span>
                      <span className="font-mono text-slate-300">{match.match_type.replace('_', ' ')}</span>
                    </div>
                  </div>

                  {isHighSim && (
                    <div className="text-[11px] text-rose-300/90 pt-1 font-medium">
                      ⚠️ Potential visual duplicate across cases. Requires underwriting investigation.
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* pHash vs Embedding Comparison Diagnostic Card */}
        <div className="mt-3 p-3 bg-slate-900/80 rounded-lg border border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
            <Layers className="h-3.5 w-3.5 text-indigo-400" />
            <span>Multi-Layer Visual Forensics Diagnostic: pHash vs Deep Visual Feature Similarity</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] text-slate-400 pt-1">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800/70 space-y-1">
              <div className="text-slate-200 font-semibold font-mono">1. Perceptual Hash (pHash)</div>
              <div>• 64-bit DCT-based frequency hash</div>
              <div>• Fast $O(1)$ Hamming distance comparison</div>
              <div>• Sensitive to identical crops, recompression, and direct re-uploads</div>
            </div>
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800/70 space-y-1">
              <div className="text-slate-200 font-semibold font-mono">2. Deep Feature Embeddings (ResNet-18)</div>
              <div>• 512-dimensional continuous feature representation</div>
              <div>• Cosine similarity over normalized unit sphere</div>
              <div>• Resilient to lighting changes, minor framing shifts, and resolution alterations</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Underwriting Disclaimers */}
      <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 shrink-0 text-slate-500 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-300">Underwriting Telemetry Notice:</span> Deep visual feature similarity is evidence of visual similarity and may indicate potentially related evidence requiring review. It does not determine fraud. Missing EXIF metadata does not prove image manipulation.
          </div>
        </div>
      </div>
    </div>
  );
};

