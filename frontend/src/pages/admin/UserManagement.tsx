/**
 * User Management Page (Phase 3.2.1)
 *
 * Admin page for managing all users in the system
 * Features:
 * - User table with sorting, filtering, and search
 * - Create new user with modal form
 * - Edit user role and details
 * - Deactivate/reactivate users
 * - Bulk upload users from CSV
 * - Real-time search and filters
 * - Pagination with infinite scroll
 *
 * Uses:
 * - DataTable component (Phase 2.1)
 * - StatsCard component (Phase 2.1)
 * - React Query for server state management
 * - React Hook Form for form validation
 */

import React, { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users,
  UserPlus,
  Search,
  Filter,
  Download,
  Upload,
  RefreshCw,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Mail,
  GraduationCap,
  BookOpen,
  Shield,
} from 'lucide-react'
import { adminApi, UserResponse } from '../../api/admin'
import { useToast } from '../../hooks/useToast'
import { StatsCard } from '../../components/StatsCard'
import { CreateUserModal } from '../../components/CreateUserModal'
import { EditUserModal } from '../../components/EditUserModal'
import { BulkUploadModal } from '../../components/BulkUploadModal'

/**
 * Role badge component
 */
const RoleBadge: React.FC<{ role: string }> = ({ role }) => {
  const colors = {
    student: 'bg-blue-100 text-blue-700 border-blue-200',
    teacher: 'bg-purple-100 text-purple-700 border-purple-200',
    admin: 'bg-orange-100 text-orange-700 border-orange-200',
    super_admin: 'bg-red-100 text-red-700 border-red-200',
  }

  const icons = {
    student: GraduationCap,
    teacher: BookOpen,
    admin: Shield,
    super_admin: Shield,
  }

  const colorClass = colors[role as keyof typeof colors] || 'bg-gray-100 text-gray-700'
  const Icon = icons[role as keyof typeof icons] || Users

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${colorClass}`}
    >
      <Icon className="w-3 h-3" />
      {role.replace('_', ' ')}
    </span>
  )
}

/**
 * Status badge component
 */
const StatusBadge: React.FC<{ isActive: boolean }> = ({ isActive }) => {
  return isActive ? (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
      <CheckCircle className="w-3 h-3" />
      Active
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
      <XCircle className="w-3 h-3" />
      Inactive
    </span>
  )
}

/**
 * User Management Page Component
 */
export const UserManagement: React.FC = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  // State
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isBulkUploadModalOpen, setIsBulkUploadModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<UserResponse | null>(null)
  const [cursor, setCursor] = useState<string | undefined>()

  // Fetch users
  const {
    data: usersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['admin-users', roleFilter, searchQuery, cursor],
    queryFn: () =>
      adminApi.listUsers({
        role: roleFilter || undefined,
        search: searchQuery || undefined,
        limit: 50,
        cursor,
      }),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: (_, userId) => {
      toast({
        title: 'User Deactivated',
        description: 'User has been deactivated successfully.',
        variant: 'success',
      })
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError: (error: any) => {
      toast({
        title: 'Deactivation Failed',
        description: error.response?.data?.detail || 'Failed to deactivate user',
        variant: 'error',
      })
    },
  })

  // Filter users by status (client-side)
  const filteredUsers = useMemo(() => {
    if (!usersData?.users) return []

    return usersData.users.filter((user) => {
      if (statusFilter === 'active') return user.is_active
      if (statusFilter === 'inactive') return !user.is_active
      return true
    })
  }, [usersData, statusFilter])

  // Handle delete user
  const handleDeleteUser = (user: UserResponse) => {
    if (
      window.confirm(
        `Are you sure you want to deactivate ${user.first_name} ${user.last_name}? This action can be undone.`
      )
    ) {
      deleteUserMutation.mutate(user.user_id)
    }
  }

  // Loading state
  if (isLoading && !usersData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading users...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load users</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
              <p className="mt-2 text-gray-600">
                Manage all users, roles, and permissions in the system
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsBulkUploadModalOpen(true)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Bulk Upload
              </button>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <UserPlus className="w-4 h-4" />
                Create User
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatsCard
              title="Total Users"
              value={stats.total_users.toString()}
              icon={Users}
              trend={
                stats.total_users > 0
                  ? { value: stats.total_users, direction: 'up' as const, label: 'total' }
                  : undefined
              }
            />
            <StatsCard
              title="Students"
              value={stats.total_students.toString()}
              icon={GraduationCap}
              trend={
                stats.total_students > 0
                  ? {
                      value: stats.total_students,
                      direction: 'neutral' as const,
                      label: 'enrolled',
                    }
                  : undefined
              }
            />
            <StatsCard
              title="Teachers"
              value={stats.total_teachers.toString()}
              icon={BookOpen}
              trend={
                stats.total_teachers > 0
                  ? { value: stats.total_teachers, direction: 'neutral' as const, label: 'active' }
                  : undefined
              }
            />
            <StatsCard
              title="Active Today"
              value={stats.active_users_today.toString()}
              icon={CheckCircle}
              trend={
                stats.active_users_today > 0
                  ? {
                      value: Math.round((stats.active_users_today / stats.total_users) * 100),
                      direction: 'up' as const,
                      label: 'engagement',
                      isPercentage: true,
                    }
                  : undefined
              }
            />
          </div>

          {/* Filters and Search */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Search */}
                <div className="md:col-span-2">
                  <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                    <Search className="w-4 h-4 inline mr-1" />
                    Search Users
                  </label>
                  <input
                    id="search"
                    type="text"
                    placeholder="Search by name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Role Filter */}
                <div>
                  <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                    <Filter className="w-4 h-4 inline mr-1" />
                    Role
                  </label>
                  <select
                    id="role"
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Roles</option>
                    <option value="student">Student</option>
                    <option value="teacher">Teacher</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>

                {/* Status Filter */}
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                    <Filter className="w-4 h-4 inline mr-1" />
                    Status
                  </label>
                  <select
                    id="status"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as any)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* User Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Login
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                        <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                        <p className="font-medium mb-2">No users found</p>
                        <p className="text-sm">Try adjusting your filters or search query</p>
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((user) => (
                      <tr key={user.user_id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
                                <span className="text-white font-medium text-sm">
                                  {user.first_name[0]}
                                  {user.last_name[0]}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {user.first_name} {user.last_name}
                              </div>
                              {user.grade_level && (
                                <div className="text-sm text-gray-500">Grade {user.grade_level}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center text-sm text-gray-900">
                            <Mail className="w-4 h-4 mr-2 text-gray-400" />
                            {user.email}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <RoleBadge role={user.role} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge isActive={user.is_active} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.last_login_at
                            ? new Date(user.last_login_at).toLocaleDateString()
                            : 'Never'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setEditingUser(user)}
                              className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                            >
                              <Edit className="w-4 h-4" />
                              Edit
                            </button>
                            {user.is_active && (
                              <button
                                onClick={() => handleDeleteUser(user)}
                                disabled={deleteUserMutation.isPending}
                                className="text-red-600 hover:text-red-900 flex items-center gap-1 disabled:opacity-50"
                              >
                                <Trash2 className="w-4 h-4" />
                                Deactivate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {usersData?.pagination.has_more && (
              <div className="px-6 py-4 border-t border-gray-200">
                <button
                  onClick={() => setCursor(usersData.pagination.next_cursor)}
                  className="w-full px-4 py-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Load More Users
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={(user) => {
          toast({
            title: 'User Created',
            description: `${user.first_name} ${user.last_name} has been created successfully.`,
            variant: 'success',
          })
          queryClient.invalidateQueries({ queryKey: ['admin-users'] })
          queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
          setIsCreateModalOpen(false)
        }}
      />

      {/* Edit User Modal */}
      {editingUser && (
        <EditUserModal
          isOpen={!!editingUser}
          onClose={() => setEditingUser(null)}
          user={editingUser}
          onSuccess={(user) => {
            toast({
              title: 'User Updated',
              description: `${user.first_name} ${user.last_name} has been updated successfully.`,
              variant: 'success',
            })
            queryClient.invalidateQueries({ queryKey: ['admin-users'] })
            setEditingUser(null)
          }}
        />
      )}

      {/* Bulk Upload Modal */}
      <BulkUploadModal
        isOpen={isBulkUploadModalOpen}
        onClose={() => setIsBulkUploadModalOpen(false)}
        onSuccess={(result) => {
          toast({
            title: 'Bulk Upload Complete',
            description: `Successfully created ${result.successful} users. ${result.failed} failed.`,
            variant: result.failed > 0 ? 'warning' : 'success',
          })
          queryClient.invalidateQueries({ queryKey: ['admin-users'] })
          queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
          setIsBulkUploadModalOpen(false)
        }}
      />
    </div>
  )
}

export default UserManagement
