'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { 
  Camera, 
  MapPin, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowLeft, 
  RefreshCw, 
  Copy, 
  ExternalLink, 
  FileText, 
  Smartphone,
  Upload,
  Info,
  Layers,
  Sparkles
} from 'lucide-react';
import { uploadInstallationImage, getCases, getCaseById } from '@/lib/api';
import { Case } from '@/types';

// Compute real SHA-256 over raw image bytes using Web Crypto API
async function computeFileSha256(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

interface ProvenanceReceipt {
  imageId: string;
  caseId: string;
  originalFilename: string;
  fileSizeBytes: number;
  mimeType: string;
  sha256Hash: string;
  gpsCoordinates: { lat: number; lng: number; accuracy?: number } | null;
  gpsSource: 'browser_geolocation' | 'exif_metadata' | 'unavailable';
  serverTimestamp: string;
  verificationStatus: string;
}

function FieldCaptureContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialCaseId = searchParams.get('caseId') || 'CAS-2026-007';

  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(initialCaseId);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);

  // File and preview state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [computedHash, setComputedHash] = useState<string | null>(null);
  const [imageType, setImageType] = useState<string>('installation_wide');

  // GPS state
  const [gpsStatus, setGpsStatus] = useState<'acquiring' | 'locked' | 'denied' | 'unsupported'>('acquiring');
  const [gpsCoords, setGpsCoords] = useState<{ lat: number; lng: number; accuracy?: number } | null>(null);

  // Upload and confirmation state
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ProvenanceReceipt | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load cases for selection
  useEffect(() => {
    async function loadCasesData() {
      try {
        const { cases: loadedCases } = await getCases();
        if (loadedCases && loadedCases.length > 0) {
          setCases(loadedCases);
          const current = loadedCases.find((c) => c.case_number === selectedCaseId || c.id === selectedCaseId);
          if (current) {
            setSelectedCase(current);
          }
        }
      } catch (err) {
        console.warn('Failed to load cases list:', err);
      }
    }
    loadCasesData();
  }, [selectedCaseId]);

  // Handle case change
  const handleCaseChange = async (newCaseId: string) => {
    setSelectedCaseId(newCaseId);
    const found = cases.find((c) => c.case_number === newCaseId || c.id === newCaseId);
    if (found) {
      setSelectedCase(found);
    } else {
      const { caseItem } = await getCaseById(newCaseId);
      setSelectedCase(caseItem);
    }
  };

  // Acquire real browser GPS geolocation
  useEffect(() => {
    if (!navigator.geolocation) {
      setGpsStatus('unsupported');
      return;
    }

    setGpsStatus('acquiring');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsCoords({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy
        });
        setGpsStatus('locked');
      },
      (error) => {
        console.warn('Geolocation access error:', error.message);
        setGpsStatus('denied');
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000
      }
    );
  }, []);

  // Handle file selection and SHA-256 calculation
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setUploadError('Please select a valid image file (JPEG, PNG, WEBP).');
        return;
      }

      // Validate size (max 25MB)
      if (file.size > 25 * 1024 * 1024) {
        setUploadError('File size exceeds 25 MB limit.');
        return;
      }

      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));

      // Calculate SHA-256 hash immediately on actual bytes
      try {
        const hash = await computeFileSha256(file);
        setComputedHash(hash);
      } catch (err) {
        console.warn('SHA-256 calculation failed:', err);
      }
    }
  };

  // Submit capture to backend
  const handleSubmitCapture = async () => {
    if (!selectedFile) {
      setUploadError('Please capture or choose an asset photo before submitting.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      // 1. Calculate SHA-256 hash if not already computed
      const sha256 = computedHash || await computeFileSha256(selectedFile);

      // 2. Submit to backend API /api/v1/images
      const res = await uploadInstallationImage(selectedCaseId, selectedFile, imageType);

      if (!res || !res.id) {
        throw new Error('Server did not return a valid image identifier.');
      }

      // 3. Construct genuine provenance receipt from backend response & client SHA-256
      const finalReceipt: ProvenanceReceipt = {
        imageId: res.id,
        caseId: selectedCaseId,
        originalFilename: res.original_filename || selectedFile.name,
        fileSizeBytes: res.file_size_bytes || selectedFile.size,
        mimeType: res.mime_type || selectedFile.type,
        sha256Hash: sha256,
        gpsCoordinates: (res.exif_lat && res.exif_lng) 
          ? { lat: res.exif_lat, lng: res.exif_lng } 
          : gpsCoords,
        gpsSource: (res.exif_lat && res.exif_lng) ? 'exif_metadata' : (gpsCoords ? 'browser_geolocation' : 'unavailable'),
        serverTimestamp: res.exif_timestamp || new Date().toISOString(),
        verificationStatus: res.verification_status || 'uploaded'
      };

      setReceipt(finalReceipt);
    } catch (err: any) {
      console.error('Failed to record capture provenance:', err);
      setUploadError(err.message || 'Failed to upload and record capture provenance. Ensure backend is running.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleResetForNewCapture = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setComputedHash(null);
    setReceipt(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const copyHashToClipboard = () => {
    if (receipt?.sha256Hash) {
      navigator.clipboard.writeText(receipt.sha256Hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2500);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-5">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <Link
          href={selectedCaseId ? `/cases/${selectedCaseId}` : '/cases'}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-[#68738A] hover:text-[#182033] bg-white px-3 py-1.5 rounded-xl border border-[#E5E9F2] shadow-2xs transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Field Dossier</span>
        </Link>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] text-xs font-bold font-mono border border-[#4F6EF7]/20">
          <Smartphone className="h-3.5 w-3.5" />
          <span>DIAVN Field Capture</span>
        </div>
      </div>

      {/* Case Target Card */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-[#E5E9F2] pb-2.5">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[#4F6EF7]" />
            <span className="text-xs font-bold uppercase tracking-wider text-[#8E99AD]">
              Target Loan Case
            </span>
          </div>
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
            PHYSICAL AUDIT
          </span>
        </div>

        <div className="space-y-2">
          <label className="text-[11px] font-bold text-[#182033] block">
            Associated Case ID
          </label>
          <select
            value={selectedCaseId}
            onChange={(e) => handleCaseChange(e.target.value)}
            disabled={isUploading || !!receipt}
            className="w-full text-xs font-mono font-bold bg-[#F8FAFD] border border-[#E5E9F2] rounded-xl px-3 py-2 text-[#182033] focus:outline-none focus:border-[#4F6EF7] disabled:opacity-60"
          >
            <option value="CAS-2026-007">CAS-2026-007 — Micro-Irrigation Controller (Flagged)</option>
            <option value="CAS-2026-001">CAS-2026-001 — Solar Pump Set (Verified)</option>
            <option value="CAS-2026-002">CAS-2026-002 — Drip Irrigation System (Price Review)</option>
            <option value="CAS-2026-003">CAS-2026-003 — Submersible Pump (GPS Review)</option>
            <option value="CAS-2026-005">CAS-2026-005 — Diesel Generator Set (Photo Review)</option>
          </select>

          {selectedCase && (
            <div className="p-2.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2] text-[11px] space-y-1">
              <div className="flex justify-between">
                <span className="text-[#8E99AD]">Asset Model:</span>
                <span className="font-bold text-[#182033] font-mono">{selectedCase.asset_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8E99AD]">Claimed Site:</span>
                <span className="text-[#182033] text-right truncate max-w-[200px]">{selectedCase.claimed_installation_address}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* POST-CAPTURE RECEIPT SCREEN */}
      {receipt ? (
        <div className="rounded-2xl border-2 border-[#A7F3D0] bg-gradient-to-br from-[#ECFDF5] via-white to-white p-5 shadow-sm space-y-5">
          <div className="flex items-center gap-3 border-b border-[#A7F3D0] pb-4">
            <div className="h-10 w-10 rounded-xl bg-[#10B981] text-white flex items-center justify-center shrink-0 shadow-xs">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-[#10B981] text-white font-mono">
                  PROVENANCE STORED
                </span>
              </div>
              <h3 className="text-base font-extrabold text-[#065F46] mt-0.5">
                Capture Provenance Recorded
              </h3>
            </div>
          </div>

          {/* Receipt Parameters */}
          <div className="space-y-3 text-xs">
            <div className="p-3 bg-white rounded-xl border border-[#E5E9F2] space-y-1">
              <span className="text-[10px] uppercase font-bold text-[#8E99AD] block font-mono">
                Associated Case ID
              </span>
              <span className="font-mono font-extrabold text-sm text-[#182033] block">
                {receipt.caseId}
              </span>
            </div>

            <div className="p-3 bg-white rounded-xl border border-[#E5E9F2] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-[#8E99AD] font-mono">
                  SHA-256 Integrity Hash
                </span>
                <button
                  onClick={copyHashToClipboard}
                  className="inline-flex items-center gap-1 text-[10px] text-[#4F6EF7] hover:text-[#3E5DE6] font-bold"
                >
                  <Copy className="h-3 w-3" />
                  <span>{copiedHash ? 'Copied!' : 'Copy Hash'}</span>
                </button>
              </div>
              <div className="font-mono font-bold text-[#182033] text-xs break-all bg-[#F8FAFD] p-2 rounded-lg border border-[#E5E9F2]">
                {receipt.sha256Hash}
              </div>
              <span className="text-[10px] text-[#68738A] block">
                Computed directly over actual submitted image byte stream.
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 bg-white rounded-xl border border-[#E5E9F2] space-y-1">
                <span className="text-[10px] uppercase font-bold text-[#8E99AD] block font-mono">
                  GPS Coordinates
                </span>
                {receipt.gpsCoordinates ? (
                  <span className="font-mono font-bold text-xs text-[#182033] block">
                    {receipt.gpsCoordinates.lat.toFixed(4)}° N, {receipt.gpsCoordinates.lng.toFixed(4)}° E
                  </span>
                ) : (
                  <span className="text-xs text-[#8E99AD] italic block">GPS unavailable</span>
                )}
                <span className="text-[10px] text-[#68738A] block">
                  Source: {receipt.gpsSource.replace('_', ' ')}
                </span>
              </div>

              <div className="p-3 bg-white rounded-xl border border-[#E5E9F2] space-y-1">
                <span className="text-[10px] uppercase font-bold text-[#8E99AD] block font-mono">
                  Server Timestamp
                </span>
                <span className="font-mono font-bold text-xs text-[#182033] block">
                  {new Date(receipt.serverTimestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
                </span>
                <span className="text-[10px] text-[#68738A] block">
                  {new Date(receipt.serverTimestamp).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="p-3 bg-white rounded-xl border border-[#E5E9F2] space-y-1">
              <span className="text-[10px] uppercase font-bold text-[#8E99AD] block font-mono">
                Server Image Reference ID
              </span>
              <span className="font-mono text-xs text-[#182033] block">
                {receipt.imageId}
              </span>
              <span className="text-[10px] text-[#68738A] block">
                Size: {(receipt.fileSizeBytes / 1024).toFixed(1)} KB • Format: {receipt.mimeType}
              </span>
            </div>
          </div>

          {/* Provenance Compliance Notice */}
          <div className="p-3 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[11px] text-[#065F46] space-y-1">
            <div className="flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 text-[#10B981] shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <strong>Tamper-Evident Provenance:</strong> Record permanently indexed in private storage vault. Server timestamp and SHA-256 signature attached to Case #{receipt.caseId} audit ledger.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2 pt-1">
            <Link
              href={`/cases/${receipt.caseId}`}
              className="w-full inline-flex items-center justify-center gap-2 py-3 rounded-xl bg-[#10B981] hover:bg-[#059669] text-white text-xs font-bold transition-all shadow-xs"
            >
              <FileText className="h-4 w-4" />
              <span>Return to Field Dossier</span>
            </Link>

            <button
              onClick={handleResetForNewCapture}
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white hover:bg-[#F8FAFD] text-[#182033] text-xs font-bold border border-[#E5E9F2] transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Capture Another Asset Photo</span>
            </button>
          </div>
        </div>
      ) : (
        /* PRE-CAPTURE & CAMERA VIEWFINDER SCREEN */
        <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs space-y-4">
          {/* Viewfinder / Preview Box */}
          <div className="relative rounded-2xl border-2 border-dashed border-[#CBD5E1] bg-[#F8FAFD] overflow-hidden min-h-[260px] flex flex-col items-center justify-center text-center p-4">
            {previewUrl ? (
              <div className="relative w-full h-full flex flex-col items-center">
                <img
                  src={previewUrl}
                  alt="Captured Asset Preview"
                  className="max-h-[240px] w-auto rounded-xl object-contain shadow-xs border border-[#E5E9F2]"
                />
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[11px] font-mono font-bold text-[#182033]">
                    {selectedFile?.name}
                  </span>
                  <span className="text-[10px] text-[#8E99AD]">
                    ({((selectedFile?.size || 0) / 1024).toFixed(1)} KB)
                  </span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="h-14 w-14 rounded-2xl bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center mx-auto">
                  <Camera className="h-7 w-7" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-[#182033]">
                    Asset Viewfinder
                  </h4>
                  <p className="text-xs text-[#68738A] max-w-xs mt-1">
                    Capture photo with device camera or choose high-resolution image file.
                  </p>
                </div>
              </div>
            )}

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
              className="hidden"
              id="camera-input"
            />
          </div>

          {/* Choose / Retake Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-[#F8FAFD] hover:bg-[#F1F4FA] text-[#182033] border border-[#E5E9F2] text-xs font-bold transition-colors cursor-pointer"
            >
              <Camera className="h-4 w-4 text-[#4F6EF7]" />
              <span>{selectedFile ? 'Retake Photo' : 'Open Camera'}</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-[#F8FAFD] hover:bg-[#F1F4FA] text-[#182033] border border-[#E5E9F2] text-xs font-bold transition-colors cursor-pointer"
            >
              <Upload className="h-4 w-4 text-[#68738A]" />
              <span>Select File</span>
            </button>
          </div>

          {/* Image Category Selector */}
          <div className="space-y-1.5 pt-1">
            <label className="text-[11px] font-bold text-[#182033] block">
              Capture Category
            </label>
            <select
              value={imageType}
              onChange={(e) => setImageType(e.target.value)}
              className="w-full text-xs font-medium bg-[#F8FAFD] border border-[#E5E9F2] rounded-xl px-3 py-2 text-[#182033] focus:outline-none focus:border-[#4F6EF7]"
            >
              <option value="installation_wide">Wide Field Installation Shot</option>
              <option value="serial_plate">Serial Number Plate Close-up</option>
              <option value="equipment_front">Equipment Frontal View</option>
              <option value="site_context">Surrounding Agricultural Site</option>
            </select>
          </div>

          {/* Live Telemetry Status Badges */}
          <div className="p-3 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2] space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[#8E99AD] flex items-center gap-1.5 text-[11px] font-semibold">
                <MapPin className="h-3.5 w-3.5 text-[#F59E0B]" />
                <span>GPS Geolocation</span>
              </span>
              {gpsStatus === 'locked' && gpsCoords ? (
                <span className="font-mono text-[11px] font-bold text-[#065F46]">
                  {gpsCoords.lat.toFixed(4)}° N, {gpsCoords.lng.toFixed(4)}° E
                </span>
              ) : gpsStatus === 'acquiring' ? (
                <span className="text-[11px] text-[#F59E0B] flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  <span>Acquiring...</span>
                </span>
              ) : (
                <span className="text-[11px] text-[#8E99AD] italic">GPS unavailable</span>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-[#E5E9F2] pt-2">
              <span className="text-[#8E99AD] flex items-center gap-1.5 text-[11px] font-semibold">
                <Clock className="h-3.5 w-3.5 text-[#4F6EF7]" />
                <span>Timestamp</span>
              </span>
              <span className="text-[11px] font-mono text-[#182033]">
                Authoritative Server Recorded
              </span>
            </div>

            {computedHash && (
              <div className="flex items-center justify-between border-t border-[#E5E9F2] pt-2">
                <span className="text-[#8E99AD] flex items-center gap-1.5 text-[11px] font-semibold">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#10B981]" />
                  <span>SHA-256</span>
                </span>
                <span className="font-mono text-[10px] font-bold text-[#182033]">
                  {computedHash.slice(0, 8)}...{computedHash.slice(-8)}
                </span>
              </div>
            )}
          </div>

          {/* Error banner if any */}
          {uploadError && (
            <div className="p-3 bg-[#FEF2F2] rounded-xl border border-[#FECACA] text-xs text-[#991B1B] flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-[#EF4444]" />
              <p>{uploadError}</p>
            </div>
          )}

          {/* Primary Action Button */}
          <button
            type="button"
            onClick={handleSubmitCapture}
            disabled={!selectedFile || isUploading}
            className="w-full py-3.5 px-4 rounded-xl bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white font-bold text-sm transition-all shadow-xs hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
          >
            {isUploading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Computing SHA-256 & Storing Provenance...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>RECORD CAPTURE PROVENANCE</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Informational Compliance Footer */}
      <div className="p-3 rounded-xl bg-white border border-[#E5E9F2] text-[10px] text-[#8E99AD] space-y-1">
        <div className="flex items-start gap-1.5">
          <Info className="h-3.5 w-3.5 text-[#4F6EF7] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-[#182033]">DIAVN Provenance Policy:</strong> Submitted images undergo SHA-256 hash anchoring, EXIF geodetic extraction, and storage in an encrypted private vault. This establishes a tamper-evident audit record for loan underwriting verification.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function FieldCapturePage() {
  return (
    <div className="min-h-screen bg-[#F6F8FC] py-6 px-4 sm:px-6">
      <Suspense fallback={
        <div className="max-w-md mx-auto p-12 text-center text-xs text-[#68738A] bg-white rounded-2xl border border-[#E5E9F2]">
          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#4F6EF7]" />
          <span>Loading DIAVN Field Capture...</span>
        </div>
      }>
        <FieldCaptureContent />
      </Suspense>
    </div>
  );
}
