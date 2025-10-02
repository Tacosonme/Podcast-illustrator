import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  Loader2, 
  FileAudio, 
  MessageSquare, 
  Image, 
  CheckCircle, 
  AlertCircle,
  Clock
} from 'lucide-react'
import { motion } from 'framer-motion'

const ProcessingStatus = ({ jobStatus, currentJob }) => {
  if (!currentJob) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">No job in progress</p>
        </CardContent>
      </Card>
    )
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      case 'processing': return 'bg-blue-500'
      case 'analyzing': return 'bg-purple-500'
      case 'generating': return 'bg-orange-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5" />
      case 'failed': return <AlertCircle className="h-5 w-5" />
      default: return <Loader2 className="h-5 w-5 animate-spin" />
    }
  }

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const getProcessingSteps = () => {
    const progress = jobStatus?.progress || 0
    
    return [
      {
        id: 'upload',
        title: 'File Upload',
        description: 'Audio file uploaded successfully',
        icon: <FileAudio className="h-4 w-4" />,
        completed: true,
        active: false
      },
      {
        id: 'transcription',
        title: 'Audio Transcription',
        description: 'Converting speech to text with timestamps',
        icon: <MessageSquare className="h-4 w-4" />,
        completed: progress >= 70,
        active: progress > 0 && progress < 70
      },
      {
        id: 'analysis',
        title: 'Content Analysis',
        description: 'Analyzing content for visual opportunities',
        icon: <Image className="h-4 w-4" />,
        completed: progress >= 90,
        active: progress >= 70 && progress < 90
      },
      {
        id: 'generation',
        title: 'Visual Generation',
        description: 'Creating images and visual content',
        icon: <Image className="h-4 w-4" />,
        completed: progress >= 98,
        active: progress >= 90 && progress < 98
      }
    ]
  }

  const steps = getProcessingSteps()

  return (
    <div className="space-y-6">
      {/* Job Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(jobStatus?.status)}
                Processing Status
              </CardTitle>
              <CardDescription>
                Job ID: {currentJob.job_id}
              </CardDescription>
            </div>
            <Badge className={`${getStatusColor(jobStatus?.status)} text-white`}>
              {jobStatus?.status || 'Unknown'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
            <div>
              <p className="text-sm font-medium">Filename</p>
              <p className="text-sm text-muted-foreground">{currentJob.filename}</p>
            </div>
            <div>
              <p className="text-sm font-medium">File Size</p>
              <p className="text-sm text-muted-foreground">
                {Math.round(currentJob.file_size / (1024 * 1024))} MB
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Duration</p>
              <p className="text-sm text-muted-foreground">
                {formatDuration(currentJob.duration || 0)}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{jobStatus?.progress || 0}%</span>
            </div>
            <Progress value={jobStatus?.progress || 0} className="w-full" />
          </div>

          {/* Status Message */}
          {jobStatus?.message && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>{jobStatus.message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Processing Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Pipeline</CardTitle>
          <CardDescription>
            Track the progress of each processing step
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center space-x-4 p-4 rounded-lg border transition-all duration-200 ${
                  step.active 
                    ? 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20' 
                    : step.completed 
                    ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                    : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/20'
                }`}
              >
                <div className={`p-2 rounded-full ${
                  step.active 
                    ? 'bg-blue-500 text-white' 
                    : step.completed 
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-300 text-gray-600 dark:bg-gray-600 dark:text-gray-300'
                }`}>
                  {step.completed ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : step.active ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    step.icon
                  )}
                </div>
                
                <div className="flex-1">
                  <h4 className="font-medium">{step.title}</h4>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
                
                <div>
                  {step.completed && (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Complete
                    </Badge>
                  )}
                  {step.active && (
                    <Badge variant="outline" className="text-blue-600 border-blue-600">
                      In Progress
                    </Badge>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {jobStatus?.status === 'failed' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Processing failed: {jobStatus.message}
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default ProcessingStatus

