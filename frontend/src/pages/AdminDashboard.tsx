import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { useAuthStore } from '../store/authStore'

export const AdminDashboard: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-display font-bold">
            Organization Admin Dashboard
          </h1>
          <p className="text-muted-foreground mt-2">
            Welcome, {user?.first_name}! Manage your organization's schools and students
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Schools</CardTitle>
              <CardDescription>Manage schools in your organization</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Content Requests</CardTitle>
              <CardDescription>Review and approve content requests</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Analytics</CardTitle>
              <CardDescription>View organization-wide metrics</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default AdminDashboard
