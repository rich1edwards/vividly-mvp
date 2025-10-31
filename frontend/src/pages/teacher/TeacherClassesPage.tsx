/**
 * Teacher Classes Page
 *
 * Manage and view all classes
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { CenteredLoading } from '../../components/ui/Loading'
import { useToast } from '../../hooks/useToast'
import { teacherApi } from '../../api/teacher'
import type { Class } from '../../types'

export const TeacherClassesPage: React.FC = () => {
  const navigate = useNavigate()
  const { success, error: showError } = useToast()

  const [classes, setClasses] = useState<Class[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    loadClasses()
  }, [])

  const loadClasses = async () => {
    try {
      setIsLoading(true)
      const data = await teacherApi.getClasses()
      setClasses(data)
    } catch (error: any) {
      showError('Failed to load classes', error.response?.data?.detail || 'Please try again')
    } finally {
      setIsLoading(false)
    }
  }

  const filteredClasses = classes.filter((cls) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        cls.name.toLowerCase().includes(query) ||
        cls.subject.toLowerCase().includes(query) ||
        cls.grade_level.toString().includes(query)
      )
    }
    return true
  })

  const handleDeleteClass = async (classId: string, className: string) => {
    if (!confirm(`Are you sure you want to delete "${className}"? This action cannot be undone.`)) {
      return
    }

    try {
      await teacherApi.deleteClass(classId)
      setClasses(classes.filter((c) => c.class_id !== classId))
      success('Class deleted', `"${className}" has been removed`)
    } catch (error: any) {
      showError('Delete failed', error.response?.data?.detail || 'Please try again')
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold text-foreground">My Classes</h1>
            <p className="text-muted-foreground mt-2">
              {classes.length} class{classes.length !== 1 ? 'es' : ''} total
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            }
          >
            Create Class
          </Button>
        </div>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="relative">
              <input
                type="text"
                placeholder="Search classes by name, subject, or grade..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 pl-10 pr-4 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* Classes List */}
        {isLoading ? (
          <CenteredLoading message="Loading classes..." />
        ) : filteredClasses.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  {searchQuery ? 'No classes found' : 'No classes yet'}
                </h3>
                <p className="text-muted-foreground mb-6">
                  {searchQuery ? 'Try adjusting your search' : 'Create your first class to get started!'}
                </p>
                {!searchQuery && (
                  <Button variant="primary" onClick={() => setShowCreateModal(true)}>
                    Create Class
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClasses.map((cls) => (
              <Card
                key={cls.class_id}
                variant="elevated"
                interactive
                onClick={() => navigate(`/teacher/classes/${cls.class_id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-1">{cls.name}</CardTitle>
                      <CardDescription>
                        {cls.subject} • Grade {cls.grade_level}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {cls.description && (
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {cls.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                      </svg>
                      <span>{cls.student_count || 0} students</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      fullWidth
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/teacher/classes/${cls.class_id}`)
                      }}
                    >
                      View Details
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteClass(cls.class_id, cls.name)
                      }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Class Modal */}
      {showCreateModal && (
        <CreateClassModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={(newClass) => {
            setClasses([newClass, ...classes])
            setShowCreateModal(false)
            success('Class created', `"${newClass.name}" is ready for students`)
          }}
        />
      )}
    </DashboardLayout>
  )
}

interface CreateClassModalProps {
  onClose: () => void
  onSuccess: (cls: Class) => void
}

const CreateClassModal: React.FC<CreateClassModalProps> = ({ onClose, onSuccess }) => {
  const { error: showError } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    grade_level: 9,
    description: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!formData.name.trim()) newErrors.name = 'Class name is required'
    if (!formData.subject.trim()) newErrors.subject = 'Subject is required'
    if (formData.grade_level < 1 || formData.grade_level > 12) {
      newErrors.grade_level = 'Grade level must be between 1 and 12'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    try {
      setIsSubmitting(true)
      const newClass = await teacherApi.createClass(formData)
      onSuccess(newClass)
    } catch (error: any) {
      showError('Creation failed', error.response?.data?.detail || 'Please try again')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create New Class</CardTitle>
          <CardDescription>Set up a new class for your students</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Class Name"
              placeholder="e.g., Advanced Biology, Algebra II"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={errors.name}
              required
            />
            <Input
              label="Subject"
              placeholder="e.g., Science, Mathematics"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              error={errors.subject}
              required
            />
            <Input
              label="Grade Level"
              type="number"
              min={1}
              max={12}
              value={formData.grade_level}
              onChange={(e) => setFormData({ ...formData, grade_level: parseInt(e.target.value) })}
              error={errors.grade_level}
              required
            />
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the class..."
                className="w-full min-h-[100px] px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-y"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>
                Create Class
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default TeacherClassesPage
