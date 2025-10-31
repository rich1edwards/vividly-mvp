import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { useAuthStore } from '../store/authStore'

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-display font-bold">
            Welcome, {user?.first_name}!
          </h1>
          <p className="text-muted-foreground mt-2">Teacher Dashboard</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Your Classes</CardTitle>
            <CardDescription>Manage your classes and track student progress</CardDescription>
          </CardHeader>
        </Card>
      </div>
    </DashboardLayout>
  )
}

export default TeacherDashboard
