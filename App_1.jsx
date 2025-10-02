import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { 
  Upload, 
  Play, 
  Download, 
  Image, 
  Video, 
  FileAudio, 
  Sparkles, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import FileUpload from './components/FileUpload'
import ProcessingStatus from './components/ProcessingStatus'
import VisualPreview from './components/VisualPreview'
import VideoPlayer from './components/VideoPlayer'
import './App.css'

function App() {
  const [currentJob, setCurrentJob] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [activeTab, setActiveTab] = useState('upload')
  const [visualContent, setVisualContent] = useState(null)
  const [videoInfo, setVideoInfo] = useState(null)

  const handleFileUpload = useCallback(async (file) => {
    try {
      const formData = new FormData()
      formData.append('audio', file)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      setCurrentJob(result)
      setActiveTab('processing')
      
      // Start processing automatically
      await startProcessing(result.job_id)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed: ' + error.message)
    }
  }, [])

  const startProcessing = async (jobId) => {
    try {
      // Start audio processing
      const processResponse = await fetch(`/api/process/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment_duration: 600,
          generate_images: true,
          generate_videos: false
        })
      })

      if (!processResponse.ok) {
        throw new Error('Processing failed to start')
      }

      // Poll for status updates
      pollJobStatus(jobId)
    } catch (error) {
      console.error('Processing error:', error)
      alert('Processing failed: ' + error.message)
    }
  }

  const pollJobStatus = async (jobId) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`)
        const status = await response.json()
        setJobStatus(status)

        if (status.status === 'completed') {
          // Audio processing complete, start content analysis
          await analyzeContent(jobId)
        } else if (status.status === 'failed') {
          console.error('Job failed:', status.message)
        } else if (status.status !== 'completed') {
          // Continue polling
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Status polling error:', error)
        setTimeout(poll, 5000) // Retry after 5 seconds
      }
    }
    poll()
  }

  const analyzeContent = async (jobId) => {
    try {
      // Analyze content for visual opportunities
      const analyzeResponse = await fetch(`/api/analyze/${jobId}`, {
        method: 'POST'
      })

      if (analyzeResponse.ok) {
        // Generate visual content
        await generateVisualContent(jobId)
      }
    } catch (error) {
      console.error('Content analysis error:', error)
    }
  }

  const generateVisualContent = async (jobId) => {
    try {
      const generateResponse = await fetch(`/api/generate/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_queries: 15,
          generate_videos: false
        })
      })

      if (generateResponse.ok) {
        const result = await generateResponse.json()
        
        // Load visual content
        const contentResponse = await fetch(`/api/content/${jobId}`)
        if (contentResponse.ok) {
          const content = await contentResponse.json()
          setVisualContent(content)
          setActiveTab('preview')
        }
      }
    } catch (error) {
      console.error('Visual content generation error:', error)
    }
  }

  const composeVideo = async () => {
    if (!currentJob) return

    try {
      setJobStatus({ status: 'composing', progress: 95, message: 'Creating final video...' })
      
      const response = await fetch(`/api/compose/${currentJob.job_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })

      if (response.ok) {
        const result = await response.json()
        setVideoInfo(result)
        setJobStatus({ status: 'completed', progress: 100, message: 'Video ready for download!' })
        setActiveTab('download')
      } else {
        throw new Error('Video composition failed')
      }
    } catch (error) {
      console.error('Video composition error:', error)
      alert('Video composition failed: ' + error.message)
    }
  }

  const downloadVideo = () => {
    if (currentJob && videoInfo) {
      window.open(`/api/download/${currentJob.job_id}`, '_blank')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-purple-900 dark:to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Podcast Illustrator
            </h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Transform your podcast episodes into visually engaging videos with AI-powered illustrations and seamless audio-visual synchronization.
          </p>
        </motion.div>

        {/* Main Interface */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full max-w-6xl mx-auto">
            <TabsList className="grid w-full grid-cols-4 mb-8">
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload
              </TabsTrigger>
              <TabsTrigger value="processing" className="flex items-center gap-2" disabled={!currentJob}>
                <Loader2 className="h-4 w-4" />
                Processing
              </TabsTrigger>
              <TabsTrigger value="preview" className="flex items-center gap-2" disabled={!visualContent}>
                <Image className="h-4 w-4" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="download" className="flex items-center gap-2" disabled={!videoInfo}>
                <Download className="h-4 w-4" />
                Download
              </TabsTrigger>
            </TabsList>

            <AnimatePresence mode="wait">
              <TabsContent value="upload" className="space-y-6">
                <motion.div
                  key="upload"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <Card className="border-dashed border-2 border-purple-200 dark:border-purple-800">
                    <CardHeader className="text-center">
                      <CardTitle className="flex items-center justify-center gap-2">
                        <FileAudio className="h-5 w-5" />
                        Upload Your Podcast
                      </CardTitle>
                      <CardDescription>
                        Upload an audio file to get started. Supported formats: MP3, WAV, M4A, FLAC, OGG
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <FileUpload onFileUpload={handleFileUpload} />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5" />
                        How It Works
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="text-center space-y-2">
                          <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full w-fit mx-auto">
                            <FileAudio className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                          </div>
                          <h3 className="font-semibold">1. Transcribe</h3>
                          <p className="text-sm text-muted-foreground">
                            AI transcribes your podcast and analyzes content for visual opportunities
                          </p>
                        </div>
                        <div className="text-center space-y-2">
                          <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-full w-fit mx-auto">
                            <Image className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                          </div>
                          <h3 className="font-semibold">2. Illustrate</h3>
                          <p className="text-sm text-muted-foreground">
                            Generate and find relevant images to illustrate key moments
                          </p>
                        </div>
                        <div className="text-center space-y-2">
                          <div className="p-3 bg-green-100 dark:bg-green-900 rounded-full w-fit mx-auto">
                            <Video className="h-6 w-6 text-green-600 dark:text-green-400" />
                          </div>
                          <h3 className="font-semibold">3. Compose</h3>
                          <p className="text-sm text-muted-foreground">
                            Combine audio with visuals to create an engaging video
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </TabsContent>

              <TabsContent value="processing" className="space-y-6">
                <motion.div
                  key="processing"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <ProcessingStatus 
                    jobStatus={jobStatus} 
                    currentJob={currentJob}
                  />
                </motion.div>
              </TabsContent>

              <TabsContent value="preview" className="space-y-6">
                <motion.div
                  key="preview"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <Image className="h-5 w-5" />
                            Visual Content Preview
                          </CardTitle>
                          <CardDescription>
                            Review the generated images before creating the final video
                          </CardDescription>
                        </div>
                        <Button onClick={composeVideo} className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600">
                          <Video className="h-4 w-4 mr-2" />
                          Create Video
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <VisualPreview visualContent={visualContent} />
                    </CardContent>
                  </Card>
                </motion.div>
              </TabsContent>

              <TabsContent value="download" className="space-y-6">
                <motion.div
                  key="download"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <Card>
                    <CardHeader className="text-center">
                      <CardTitle className="flex items-center justify-center gap-2 text-green-600">
                        <CheckCircle className="h-6 w-6" />
                        Video Ready!
                      </CardTitle>
                      <CardDescription>
                        Your illustrated podcast video has been created successfully
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {videoInfo && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                          <div>
                            <p className="text-2xl font-bold text-purple-600">{Math.round(videoInfo.total_duration / 60)}m</p>
                            <p className="text-sm text-muted-foreground">Duration</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-blue-600">{videoInfo.timeline_segments}</p>
                            <p className="text-sm text-muted-foreground">Segments</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-green-600">{Math.round(videoInfo.file_size / (1024 * 1024))}MB</p>
                            <p className="text-sm text-muted-foreground">File Size</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-orange-600">1080p</p>
                            <p className="text-sm text-muted-foreground">Quality</p>
                          </div>
                        </div>
                      )}

                      <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Button 
                          onClick={downloadVideo} 
                          size="lg"
                          className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600"
                        >
                          <Download className="h-5 w-5 mr-2" />
                          Download Video
                        </Button>
                        <Button 
                          variant="outline" 
                          size="lg"
                          onClick={() => {
                            setCurrentJob(null)
                            setJobStatus(null)
                            setVisualContent(null)
                            setVideoInfo(null)
                            setActiveTab('upload')
                          }}
                        >
                          Create Another
                        </Button>
                      </div>

                      {currentJob && (
                        <VideoPlayer jobId={currentJob.job_id} />
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              </TabsContent>
            </AnimatePresence>
          </Tabs>
        </motion.div>
      </div>
    </div>
  )
}

export default App

