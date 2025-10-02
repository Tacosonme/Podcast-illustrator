import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx'
import { 
  Image, 
  Video, 
  Clock, 
  Search, 
  Sparkles, 
  Eye,
  Grid3X3,
  List
} from 'lucide-react'
import { motion } from 'framer-motion'

const VisualPreview = ({ visualContent }) => {
  const [viewMode, setViewMode] = useState('grid')
  const [selectedImage, setSelectedImage] = useState(null)

  if (!visualContent) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
              <Image className="h-8 w-8 text-gray-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">No Visual Content Yet</h3>
              <p className="text-muted-foreground">
                Visual content will appear here once processing is complete
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const { images = [], videos = [] } = visualContent
  const totalContent = images.length + videos.length

  const formatTimestamp = (timestamp) => {
    const minutes = Math.floor(timestamp / 60)
    const seconds = Math.floor(timestamp % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const getSourceIcon = (source) => {
    switch (source) {
      case 'search': return <Search className="h-3 w-3" />
      case 'generated': return <Sparkles className="h-3 w-3" />
      default: return <Image className="h-3 w-3" />
    }
  }

  const getSourceColor = (source) => {
    switch (source) {
      case 'search': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'generated': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const ImageCard = ({ image, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="group relative"
    >
      <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-200">
        <div className="aspect-video relative bg-gray-100 dark:bg-gray-800">
          <img
            src={image.url}
            alt={image.description || 'Generated content'}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDIwMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTIwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik04NS41IDQ1TDk1IDU1TDEwNSA0NUgxMTVWNzVIODVWNDVaIiBmaWxsPSIjOUI5QkEwIi8+Cjx0ZXh0IHg9IjEwMCIgeT0iOTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM5QjlCQTAiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pgo8L3N2Zz4K'
            }}
          />
          
          {/* Overlay with actions */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
            <Dialog>
              <DialogTrigger asChild>
                <Button 
                  size="sm" 
                  variant="secondary"
                  onClick={() => setSelectedImage(image)}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>Image Preview</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <img
                    src={image.url}
                    alt={image.description}
                    className="w-full rounded-lg"
                  />
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium">Timestamp</p>
                      <p className="text-muted-foreground">{formatTimestamp(image.timestamp)}</p>
                    </div>
                    <div>
                      <p className="font-medium">Source</p>
                      <Badge className={getSourceColor(image.source)}>
                        {getSourceIcon(image.source)}
                        <span className="ml-1 capitalize">{image.source}</span>
                      </Badge>
                    </div>
                    <div className="col-span-2">
                      <p className="font-medium">Description</p>
                      <p className="text-muted-foreground">{image.description || 'No description available'}</p>
                    </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Timestamp badge */}
          <div className="absolute top-2 left-2">
            <Badge variant="secondary" className="text-xs">
              <Clock className="h-3 w-3 mr-1" />
              {formatTimestamp(image.timestamp)}
            </Badge>
          </div>

          {/* Source badge */}
          <div className="absolute top-2 right-2">
            <Badge className={`text-xs ${getSourceColor(image.source)}`}>
              {getSourceIcon(image.source)}
              <span className="ml-1 capitalize">{image.source}</span>
            </Badge>
          </div>
        </div>

        <CardContent className="p-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {image.description || image.query || 'Generated visual content'}
          </p>
          {image.relevance_score && (
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Relevance</span>
                <span>{Math.round(image.relevance_score * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1">
                <div 
                  className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${image.relevance_score * 100}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )

  const ListView = ({ items }) => (
    <div className="space-y-3">
      {items.map((item, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <Card className="p-4">
            <div className="flex items-center space-x-4">
              <div className="w-20 h-12 bg-gray-100 dark:bg-gray-800 rounded overflow-hidden flex-shrink-0">
                <img
                  src={item.url}
                  alt={item.description}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <Badge variant="outline" className="text-xs">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatTimestamp(item.timestamp)}
                  </Badge>
                  <Badge className={`text-xs ${getSourceColor(item.source)}`}>
                    {getSourceIcon(item.source)}
                    <span className="ml-1 capitalize">{item.source}</span>
                  </Badge>
                </div>
                <p className="text-sm font-medium truncate">{item.description || item.query}</p>
                {item.relevance_score && (
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-muted-foreground">Relevance:</span>
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                      <div 
                        className="bg-blue-500 h-1 rounded-full"
                        style={{ width: `${item.relevance_score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(item.relevance_score * 100)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Image className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{images.length}</p>
              <p className="text-sm text-muted-foreground">Images Generated</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Video className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{videos.length}</p>
              <p className="text-sm text-muted-foreground">Video Clips</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Sparkles className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalContent}</p>
              <p className="text-sm text-muted-foreground">Total Content</p>
            </div>
          </div>
        </Card>
      </div>

      {/* View Mode Toggle */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Generated Content</h3>
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            <Grid3X3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content Tabs */}
      <Tabs defaultValue="images" className="w-full">
        <TabsList>
          <TabsTrigger value="images" className="flex items-center gap-2">
            <Image className="h-4 w-4" />
            Images ({images.length})
          </TabsTrigger>
          {videos.length > 0 && (
            <TabsTrigger value="videos" className="flex items-center gap-2">
              <Video className="h-4 w-4" />
              Videos ({videos.length})
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="images" className="mt-6">
          {images.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">No images generated yet</p>
              </CardContent>
            </Card>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {images.map((image, index) => (
                <ImageCard key={index} image={image} index={index} />
              ))}
            </div>
          ) : (
            <ListView items={images} />
          )}
        </TabsContent>

        {videos.length > 0 && (
          <TabsContent value="videos" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {videos.map((video, index) => (
                <Card key={index} className="overflow-hidden">
                  <div className="aspect-video bg-gray-100 dark:bg-gray-800">
                    <video
                      src={video.url}
                      controls
                      className="w-full h-full"
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatTimestamp(video.timestamp)}
                      </Badge>
                      <Badge className="text-xs bg-purple-100 text-purple-800">
                        <Video className="h-3 w-3 mr-1" />
                        Generated
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {video.description || 'Generated video content'}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}

export default VisualPreview

