import React, { useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { LogOut, Upload, Send, FileText, BarChart3, MessageCircle, Brain, Database, ChevronDown, ChevronUp, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { FPTLogo } from './FPTLogo';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { useReportContext } from '../contexts/ReportContext';

interface User {
  id: string;
  email: string;
  role: string;
}


interface ReportAgentPageProps {
  user: User;
  onLogout: () => void;
}

export function ReportAgentPage({ user, onLogout }: ReportAgentPageProps) {
  const location = useLocation();
  const {
    messages,
    message,
    setMessage,
    isTyping,
    reports,
    uploadedData,
    showDataTable,
    setShowDataTable,
    chatCollapsed,
    setChatCollapsed,
    dataCollapsed,
    setDataCollapsed,
    handleFileUpload,
    sendMessage: contextSendMessage,
    clearChat: handleClearChat
  } = useReportContext();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    setMessage('');
    await contextSendMessage();
  };


  return (
    <div className="h-screen flex flex-col bg-white text-black">
      {/* Header with FPT Logo */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <FPTLogo />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <nav className="flex space-x-6">
              <Link
                to="/chat/employee"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/chat/employee'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="h-4 w-4" />
                <span>Chat</span>
              </Link>
              
              <Link
                to="/ml"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/ml'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>ML Analysis</span>
              </Link>
              
              <Link
                to="/reports"
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  location.pathname === '/reports'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-black hover:bg-gray-100'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span>Report Analysis</span>
              </Link>
              
              {user.role === 'admin' && (
                <Link
                  to="/admin/data"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                    location.pathname === '/admin/data'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:text-black hover:bg-gray-100'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span>Data Admin</span>
                </Link>
              )}
            </nav>
            
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.email}</span>
              <Button
                variant="ghost"
                onClick={onLogout}
                className="text-gray-600 hover:text-black"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 bg-gray-50 overflow-hidden">
        {/* Left Panel - Chat Discussion */}
        <div className={`border-r border-gray-200 flex flex-col bg-white relative transition-all duration-300 ${
          chatCollapsed ? 'w-12' : dataCollapsed ? 'w-full' : 'w-1/2'
        }`}>
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 bg-white flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {!chatCollapsed && (
                <>
                  <FileText className="h-6 w-6 text-green-600" />
                  <div>
                    <h2 className="text-lg font-semibold text-black">Report Discussion</h2>
                    <p className="text-sm text-gray-600">Collaborative analysis</p>
                  </div>
                </>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setChatCollapsed(!chatCollapsed)}
              className="text-gray-600 hover:text-black hover:bg-gray-100"
              title={chatCollapsed ? "Expand chat" : "Collapse chat"}
            >
              {chatCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
          </div>

        {/* Messages */}
        {!chatCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
            <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex space-x-2 max-w-xs lg:max-w-md ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={msg.sender === 'user' ? 'bg-green-600 text-white' : 'bg-black text-white text-xs'}>
                      {msg.sender === 'user' ? 'U' : 'SAGE'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`rounded-lg p-3 ${
                      msg.sender === 'user'
                        ? 'bg-green-600 text-white'
                        : 'bg-white text-black border border-gray-200'
                    }`}
                  >
                    {msg.senderName && (
                      <p className="text-xs opacity-70 mb-1">{msg.senderName}</p>
                    )}
                    {msg.sender === 'ai' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            img: ({ src, alt }) => (
                              <img 
                                src={src} 
                                alt={alt} 
                                className="rounded-lg max-w-full h-auto my-2 shadow-md" 
                                style={{ maxHeight: '200px', objectFit: 'cover' }}
                              />
                            ),
                            h1: ({ children }) => (
                              <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-2">{children}</h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="text-xl font-bold text-gray-900 mt-4 mb-2">{children}</h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="text-lg font-semibold text-gray-900 mt-4 mb-2">{children}</h3>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside space-y-1 text-gray-700 my-2">{children}</ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-inside space-y-1 text-gray-700 my-2">{children}</ol>
                            ),
                            li: ({ children }) => (
                              <li className="text-gray-700">{children}</li>
                            ),
                            p: ({ children }) => (
                              <p className="text-gray-800 mb-2 leading-relaxed">{children}</p>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold text-gray-900">{children}</strong>
                            ),
                            em: ({ children }) => (
                              <em className="italic text-gray-800">{children}</em>
                            ),
                            code: ({ children }) => (
                              <code className="bg-gray-100 text-gray-900 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                            ),
                            pre: ({ children }) => (
                              <pre className="bg-gray-100 text-gray-900 p-3 rounded-lg overflow-x-auto my-2">{children}</pre>
                            ),
                            blockquote: ({ children }) => (
                              <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 my-2">{children}</blockquote>
                            ),
                            a: ({ href, children }) => (
                              <a 
                                href={href} 
                                className="text-blue-600 hover:text-blue-800 underline"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {children}
                              </a>
                            ),
                            hr: () => (
                              <hr className="my-4 border-gray-300" />
                            ),
                            table: ({ children }) => (
                              <div className="overflow-x-auto my-4">
                                <table className="min-w-full border-collapse border border-gray-300 text-sm">
                                  {children}
                                </table>
                              </div>
                            ),
                            thead: ({ children }) => (
                              <thead className="bg-gray-100">{children}</thead>
                            ),
                            tbody: ({ children }) => (
                              <tbody className="bg-white">{children}</tbody>
                            ),
                            tr: ({ children }) => (
                              <tr className="border-b border-gray-200 hover:bg-gray-50">{children}</tr>
                            ),
                            th: ({ children }) => (
                              <th className="border border-gray-300 px-4 py-2 text-left font-semibold text-gray-900 bg-gray-100">
                                {children}
                              </th>
                            ),
                            td: ({ children }) => (
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                {children}
                              </td>
                            )
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex space-x-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-black text-white text-xs">SAGE</AvatarFallback>
                  </Avatar>
                  <div className="bg-white text-black border border-gray-200 rounded-lg p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Message Input - Fixed at bottom */}
        {!chatCollapsed && (
          <div className="p-4 border-t border-gray-200 bg-white shadow-lg">
          <form onSubmit={sendMessage} className="flex space-x-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about the report data..."
              className="flex-1 bg-white border-gray-300 text-black placeholder:text-gray-400"
              disabled={isTyping}
            />
            <Button 
              type="submit" 
              className="bg-black hover:bg-gray-800 text-white transform transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              disabled={isTyping || !message.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          </div>
        )}
      </div>

      {/* Right Panel - Report Upload & Insights */}
      <div className={`flex flex-col bg-white overflow-hidden transition-all duration-300 ${
        dataCollapsed ? 'w-12' : chatCollapsed ? 'w-full' : 'w-1/2'
      }`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-white flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDataCollapsed(!dataCollapsed)}
            className="text-gray-600 hover:text-black hover:bg-gray-100"
            title={dataCollapsed ? "Expand data panel" : "Collapse data panel"}
          >
            {dataCollapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
          {!dataCollapsed && (
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-6 w-6 text-purple-600" />
              <div>
                <h1 className="text-lg font-semibold text-black">Report Agent</h1>
                <p className="text-sm text-gray-600">Upload & analyze reports</p>
              </div>
            </div>
          )}
          <div className="w-8"></div> {/* Spacer for alignment */}
        </div>

        {!dataCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-50">
            {/* File Upload */}
            <Card className="bg-white border-gray-200">
            <CardHeader>
              <CardTitle className="flex items-center text-black">
                <Upload className="h-5 w-5 mr-2" />
                Upload Report
              </CardTitle>
              <CardDescription className="text-gray-600">
                Upload CSV or Excel files for analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
                <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <label htmlFor="report-upload" className="cursor-pointer">
                  <span className="text-black">Click to upload</span>
                  <span className="text-gray-600"> or drag and drop</span>
                  <input
                    id="report-upload"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
                <p className="text-xs text-gray-500 mt-1">CSV, Excel files up to 200MB</p>
              </div>

              {reports.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-black text-sm font-medium">Recent Reports</h4>
                  {reports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-2 bg-gray-100 rounded">
                      <span className="text-black text-sm truncate">{report.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          report.status === 'ready' ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                        }`}>
                          {report.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Preview Table */}
          {uploadedData && (
            <Card className="bg-white border-gray-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center text-black">
                      <FileText className="h-5 w-5 mr-2" />
                      Data Preview
                    </CardTitle>
                    <CardDescription className="text-gray-600">
                      Showing first {Math.min(100, uploadedData.data.length)} of {uploadedData.data.length} rows
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClearChat}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Clear data"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Clear
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowDataTable(!showDataTable)}
                      className="text-gray-600 hover:text-black"
                    >
                      {showDataTable ? (
                        <>
                          <ChevronUp className="h-4 w-4 mr-1" />
                          Hide
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-4 w-4 mr-1" />
                          Show
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              {showDataTable && (
                <CardContent className="p-0">
                  <div className="border-t border-gray-200">
                    {/* Scrollable container for both horizontal and vertical scrolling */}
                    <div 
                      className="overflow-auto border border-gray-200 rounded-lg"
                      style={{ 
                        maxHeight: '600px',
                        maxWidth: '100%'
                      }}
                    >
                      <div className="inline-block min-w-full">
                        <Table className="min-w-full">
                          <TableHeader className="bg-gray-100 sticky top-0 z-10">
                            <TableRow>
                              <TableHead 
                                className="text-black font-semibold border-r w-16 sticky left-0 bg-gray-100 z-20 shadow-sm"
                                style={{ minWidth: '60px' }}
                              >
                                #
                              </TableHead>
                              {uploadedData.data[0] && Object.keys(uploadedData.data[0]).map((key) => (
                                <TableHead 
                                  key={key} 
                                  className="text-black font-semibold border-r whitespace-nowrap px-4"
                                  style={{ minWidth: '150px' }}
                                >
                                  {key}
                                </TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {uploadedData.data.slice(0, 100).map((row, index) => (
                              <TableRow key={index} className="hover:bg-gray-50">
                                <TableCell 
                                  className="border-r font-medium text-gray-600 sticky left-0 bg-white z-10 shadow-sm"
                                  style={{ minWidth: '60px' }}
                                >
                                  {index + 1}
                                </TableCell>
                                {Object.entries(row).map(([key, value], colIndex) => (
                                  <TableCell 
                                    key={`${key}-${colIndex}`} 
                                    className="border-r text-black whitespace-nowrap px-4"
                                    style={{ minWidth: '150px' }}
                                  >
                                    {value !== null && value !== undefined ? String(value) : '-'}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                    {uploadedData.data.length > 100 && (
                      <div className="p-3 bg-gray-50 border-t border-gray-200">
                        <p className="text-sm text-gray-500 text-center">
                          Showing first 100 rows. + {uploadedData.data.length - 100} more rows available for analysis
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          )}

          </div>
        )}
      </div>
      </div>
    </div>
  );
}