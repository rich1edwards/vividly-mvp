/**
 * Student Dashboard
 *
 * Main dashboard for student users
 */

import React from 'react'
import DashboardLayout from '../../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            Welcome back, {user?.first_name}!
          </h1>
          <p className="text-muted-foreground mt-2">
            Ready to learn something new today?
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card
            variant="elevated"
            padding="lg"
            interactive
            onClick={() => navigate('/student/content/request')}
          >
            <CardHeader className="p-0 mb-4">
              <div className="h-12 w-12 rounded-full bg-vividly-blue-100 flex items-center justify-center mb-3">
                <svg
                  className="w-6 h-6 text-vividly-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </div>
              <CardTitle className="text-lg">Request New Content</CardTitle>
            </CardHeader>
            <CardDescription>
              Ask a question and get a personalized video explanation
            </CardDescription>
          </Card>

          <Card variant="elevated" padding="lg" interactive onClick={() => navigate('/student/videos')}>
            <CardHeader className="p-0 mb-4">
              <div className="h-12 w-12 rounded-full bg-vividly-purple-100 flex items-center justify-center mb-3">
                <svg
                  className="w-6 h-6 text-vividly-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <CardTitle className="text-lg">My Videos</CardTitle>
            </CardHeader>
            <CardDescription>
              View all your personalized learning videos
            </CardDescription>
          </Card>

          <Card variant="elevated" padding="lg">
            <CardHeader className="p-0 mb-4">
              <div className="h-12 w-12 rounded-full bg-vividly-green-100 flex items-center justify-center mb-3">
                <svg
                  className="w-6 h-6 text-vividly-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                  />
                </svg>
              </div>
              <CardTitle className="text-lg">My Progress</CardTitle>
            </CardHeader>
            <CardDescription>
              Track your learning achievements
            </CardDescription>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Your latest learning sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              <svg
                className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <p>No recent activity yet</p>
              <p className="text-sm mt-2">Request your first video to get started!</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

export default StudentDashboard
