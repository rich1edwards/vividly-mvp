/**
 * Bulk Upload Modal (Phase 3.2)
 *
 * Modal for bulk uploading users from CSV
 * Features:
 * - File upload with drag-and-drop
 * - CSV format validation
 * - Transaction mode selector (partial/atomic)
 * - Upload progress tracking
 * - Detailed success/error reporting
 * - CSV template download
 * - Accessible design (WCAG AA)
 */

import React, { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  X,
  Upload,
  Download,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Info,
} from 'lucide-react'
import { adminApi, BulkUploadResponse } from '../api/admin'
import { useToast } from '../hooks/useToast'

interface BulkUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (result: BulkUploadResponse) => void
}

/**
 * CSV Template
 */
const CSV_TEMPLATE = `first_name,last_name,email,role,grade_level,school_id
John,Doe,john.doe@example.com,student,10,school_hillsboro_hs
Jane,Smith,jane.smith@example.com,student,11,school_hillsboro_hs
Bob,Johnson,bob.johnson@example.com,teacher,,school_hillsboro_hs
Alice,Williams,alice.williams@example.com,admin,,`

/**
 * BulkUploadModal Component
 */
export const BulkUploadModal: React.FC<BulkUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [transactionMode, setTransactionMode] = useState<'partial' | 'atomic'>('partial')
  const [uploadResult, setUploadResult] = useState<BulkUploadResponse | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => adminApi.bulkUploadUsers(file, transactionMode),
    onSuccess: (result) => {
      setUploadResult(result)
      toast({
        title: 'Upload Complete',
        description: `Successfully created ${result.successful} users. ${result.failed} failed.`,
        variant: result.failed > 0 ? 'warning' : 'success',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Upload Failed',
        description: error.response?.data?.detail || 'Failed to upload users',
        variant: 'error',
      })
    },
  })

  // Handle file selection
  const handleFileSelect = (file: File | null) => {
    if (!file) {
      setSelectedFile(null)
      return
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      toast({
        title: 'Invalid File',
        description: 'Please select a CSV file',
        variant: 'error',
      })
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: 'File Too Large',
        description: 'File must be smaller than 10MB',
        variant: 'error',
      })
      return
    }

    setSelectedFile(file)
    setUploadResult(null)
  }

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const file = e.dataTransfer.files[0]
    handleFileSelect(file)
  }

  // Handle upload
  const handleUpload = () => {
    if (!selectedFile) return
    uploadMutation.mutate(selectedFile)
  }

  // Download CSV template
  const downloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bulk_upload_template.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  // Handle close
  const handleClose = () => {
    if (uploadResult) {
      onSuccess(uploadResult)
    }
    setSelectedFile(null)
    setUploadResult(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulk-upload-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Upload className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 id="bulk-upload-modal-title" className="text-xl font-semibold text-gray-900">
                Bulk Upload Users
              </h2>
              <p className="text-sm text-gray-600">Upload multiple users from a CSV file</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900 space-y-2">
                <p className="font-medium">CSV Format Requirements:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>
                    <strong>Required columns:</strong> first_name, last_name, email, role
                  </li>
                  <li>
                    <strong>Optional columns:</strong> grade_level (9-12 for students), school_id
                  </li>
                  <li>
                    <strong>Valid roles:</strong> student, teacher, admin
                  </li>
                  <li>
                    <strong>Max file size:</strong> 10MB
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Template Download */}
          <div>
            <button
              onClick={downloadTemplate}
              className="w-full px-4 py-3 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg hover:bg-gray-100 hover:border-gray-400 transition-colors flex items-center justify-center gap-2 text-gray-700"
            >
              <Download className="w-5 h-5" />
              Download CSV Template
            </button>
          </div>

          {/* Transaction Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Transaction Mode
            </label>
            <div className="space-y-3">
              <label className="flex items-start gap-3 p-4 border-2 border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="transaction_mode"
                  value="partial"
                  checked={transactionMode === 'partial'}
                  onChange={(e) => setTransactionMode(e.target.value as any)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Partial (Recommended)</div>
                  <div className="text-sm text-gray-600 mt-1">
                    Allow partial success. Successfully created users are kept, even if some rows
                    fail. Best for large uploads.
                  </div>
                </div>
              </label>

              <label className="flex items-start gap-3 p-4 border-2 border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="transaction_mode"
                  value="atomic"
                  checked={transactionMode === 'atomic'}
                  onChange={(e) => setTransactionMode(e.target.value as any)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Atomic (All or Nothing)</div>
                  <div className="text-sm text-gray-600 mt-1">
                    If any row fails, the entire upload is rolled back. No users are created unless
                    all succeed.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Upload CSV File</label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
                ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}
                ${selectedFile ? 'bg-white border-green-300' : ''}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                className="hidden"
              />

              {selectedFile ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-center">
                    <FileText className="w-12 h-12 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-600">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <button
                    onClick={() => handleFileSelect(null)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-center">
                    <Upload className="w-12 h-12 text-gray-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Drop CSV file here</p>
                    <p className="text-sm text-gray-600">or</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Browse Files
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Upload Results */}
          {uploadResult && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Upload Results</h3>
                <span className="text-sm text-gray-600">
                  Duration: {uploadResult.duration_seconds.toFixed(2)}s
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <div className="text-sm text-gray-600 mb-1">Total Rows</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {uploadResult.total_rows}
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <div className="text-sm text-green-700 mb-1 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    Successful
                  </div>
                  <div className="text-2xl font-bold text-green-700">
                    {uploadResult.successful}
                  </div>
                </div>
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <div className="text-sm text-red-700 mb-1 flex items-center gap-1">
                    <XCircle className="w-4 h-4" />
                    Failed
                  </div>
                  <div className="text-2xl font-bold text-red-700">{uploadResult.failed}</div>
                </div>
              </div>

              {/* Failed Rows Details */}
              {uploadResult.failed > 0 && uploadResult.results.failed_rows && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-900">Failed Rows:</h4>
                  <div className="max-h-48 overflow-y-auto space-y-2">
                    {uploadResult.results.failed_rows.map((failedRow, index) => (
                      <div
                        key={index}
                        className="bg-red-50 border border-red-200 rounded p-3 text-sm"
                      >
                        <div className="font-medium text-red-900 mb-1">
                          Row {failedRow.row_number}:
                        </div>
                        <ul className="list-disc list-inside text-red-700 space-y-1">
                          {failedRow.errors.map((error, errorIndex) => (
                            <li key={errorIndex}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              disabled={uploadMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {uploadResult ? 'Done' : 'Cancel'}
            </button>
            {!uploadResult && (
              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || uploadMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {uploadMutation.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload Users
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
