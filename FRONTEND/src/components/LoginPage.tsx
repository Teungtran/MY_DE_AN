import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { setAuthToken, setUserData } from '../utils/api';

interface LoginPageProps {
  onLogin: (userData: { email: string; role: 'customer' | 'employee' | 'admin' }) => void;
}

type ViewState = 'signin' | 'signup' | 'forgot' | 'change';

export function LoginPage({ onLogin }: LoginPageProps) {
  const [viewState, setViewState] = useState<ViewState>('signin');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [forgotPasswordClicked, setForgotPasswordClicked] = useState(false);
  
  // Sign In form state
  const [signInData, setSignInData] = useState({
    email: '',
    password: '',
    role: 'customer' as 'customer' | 'employee' | 'admin'
  });
  
  // Sign Up form state
  const [signUpData, setSignUpData] = useState({
    username: '',
    age: '',
    email: '',
    phone: '',
    address: '',
    role: 'customer' as 'customer' | 'employee' | 'admin',
    password: '',
    confirmPassword: ''
  });
  
  // Forgot Password form state
  const [forgotData, setForgotData] = useState({
    customer_name: '',
    email: ''
  });
  
  // Change Password form state
  const [changeData, setChangeData] = useState({
    customer_name: '',
    email: '',
    temp_password: '',
    new_password: ''
  });

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // TODO: Replace with actual API integration
      // const response = await authAPI.login({
      //   customer_name_or_email: signInData.email,
      //   password: signInData.password,
      // });

      // Mock authentication for development
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
      
      // Mock successful login
      const mockToken = 'mock_jwt_token_' + Math.random().toString(36).substr(2, 9);
      const userData = {
        id: Math.random().toString(36).substr(2, 9),
        email: signInData.email,
        role: signInData.role
      };
      
      setAuthToken(mockToken);
      setUserData(userData);
      onLogin(userData);
      
      toast.success('Successfully signed in!');
    } catch (error) {
      console.error('Sign in error:', error);
      toast.error('Sign in failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (signUpData.password !== signUpData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    setIsLoading(true);
    
    try {
      // TODO: Replace with actual API integration
      // await authAPI.register({
      //   customer_name: signUpData.username,
      //   address: signUpData.address,
      //   age: parseInt(signUpData.age) || 18,
      //   customer_phone: signUpData.phone,
      //   password: signUpData.password,
      //   email: signUpData.email,
      //   role: mapFrontendRoleToBackend(signUpData.role),
      // });

      // Mock successful registration
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API delay
      
      toast.success('Account created successfully! Please sign in.');
      setViewState('signin');
      // Reset form
      setSignUpData({
        username: '',
        age: '',
        email: '',
        phone: '',
        address: '',
        role: 'customer',
        password: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Sign up error:', error);
      toast.error('Account creation failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // TODO: Replace with actual API integration
      // await authAPI.forgotPassword({
      //   customer_name: forgotData.customer_name,
      //   email: forgotData.email,
      // });

      // Mock password reset
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
      
      toast.success('A new temp password has been sent to your email. Please get the temp password and change it in Change password option.');
      setForgotPasswordClicked(true);
      setChangeData({
        customer_name: forgotData.customer_name,
        email: forgotData.email,
        temp_password: '',
        new_password: ''
      });
    } catch (error) {
      console.error('Forgot password error:', error);
      toast.error('Failed to send password reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // TODO: Replace with actual API integration
      // await authAPI.changePassword({
      //   customer_name: changeData.customer_name,
      //   email: changeData.email,
      //   new_password: changeData.new_password,
      // });
      
      // Mock password change
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
      
      toast.success('Password changed successfully! Please sign in with your new password.');
      setViewState('signin');
      setForgotPasswordClicked(false);
      // Reset form
      setChangeData({
        customer_name: '',
        email: '',
        temp_password: '',
        new_password: ''
      });
    } catch (error) {
      console.error('Change password error:', error);
      toast.error('Failed to change password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-4 mb-4">
            {/* FPT Shop Logo */}
            <div className="flex items-center space-x-1">
              <div className="w-8 h-8 bg-red-500 rounded flex items-center justify-center">
                <span className="text-white font-bold text-sm">F</span>
              </div>
              <div className="w-8 h-8 bg-orange-500 rounded flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
                <span className="text-white font-bold text-sm">T</span>
              </div>
              <span className="text-gray-700 text-sm ml-1">Shop.vn</span>
            </div>
            
            <div className="text-right">
              <h1 className="text-2xl font-bold text-black">SAGE</h1>
              <p className="text-sm text-gray-600">AI Assistant</p>
            </div>
          </div>
        </div>

        <Card className="bg-white border border-gray-200 shadow-lg">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-2xl text-black mb-2">
              {viewState === 'signin' && 'Welcome back'}
              {viewState === 'signup' && 'Create your account'}
              {viewState === 'forgot' && 'Forgot Password'}
              {viewState === 'change' && 'Change Password'}
            </CardTitle>
            <p className="text-gray-600 text-sm">
              {viewState === 'signin' && 'Sign in to your SAGE account'}
              {viewState === 'signup' && 'Join SAGE - AI assistant platform'}
              {viewState === 'forgot' && 'Enter your details to reset password'}
              {viewState === 'change' && 'Enter temp password and new password'}
            </p>
          </CardHeader>
          
          <CardContent className="pt-0">
            {/* Sign In Form */}
            {viewState === 'signin' && (
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-black">Sign In</h3>
                  <p className="text-sm text-gray-600">Enter your credentials to access your account</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-black">Email or Username</Label>
                  <Input
                    id="email"
                    type="text"
                    placeholder="Enter your email or username"
                    value={signInData.email}
                    onChange={(e) => setSignInData({...signInData, email: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-black">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      value={signInData.password}
                      onChange={(e) => setSignInData({...signInData, password: e.target.value})}
                      className="bg-white border-gray-300 text-black pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role" className="text-black">Role</Label>
                  <Select value={signInData.role} onValueChange={(value: 'customer' | 'employee' | 'admin') => setSignInData({...signInData, role: value})}>
                    <SelectTrigger className="bg-white border-gray-300 text-black">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white border-gray-300">
                      <SelectItem value="customer">Customer</SelectItem>
                      <SelectItem value="employee">Employee</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex justify-between items-center">
                  <button
                    type="button"
                    onClick={() => setViewState('forgot')}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Forgot password?
                  </button>
                  {forgotPasswordClicked && (
                    <button
                      type="button"
                      onClick={() => setViewState('change')}
                      className="text-sm text-green-600 hover:text-green-800"
                    >
                      Change Password
                    </button>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-black text-white hover:bg-gray-800"
                  disabled={isLoading}
                >
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>
                
                <div className="text-center">
                  <span className="text-gray-600 text-sm">Don't have an account? </span>
                  <button
                    type="button"
                    onClick={() => setViewState('signup')}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Sign up
                  </button>
                </div>
              </form>
            )}

            {/* Sign Up Form */}
            {viewState === 'signup' && (
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-black">Sign Up</h3>
                  <p className="text-sm text-gray-600">Fill in your information to create an account</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-black">Username</Label>
                    <Input
                      id="username"
                      type="text"
                      placeholder="Enter username"
                      value={signUpData.username}
                      onChange={(e) => setSignUpData({...signUpData, username: e.target.value})}
                      className="bg-white border-gray-300 text-black"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="age" className="text-black">Age</Label>
                    <Input
                      id="age"
                      type="number"
                      placeholder="Age"
                      value={signUpData.age}
                      onChange={(e) => setSignUpData({...signUpData, age: e.target.value})}
                      className="bg-white border-gray-300 text-black"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-black">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={signUpData.email}
                    onChange={(e) => setSignUpData({...signUpData, email: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-black">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="09xxxxxxxx"
                    value={signUpData.phone}
                    onChange={(e) => setSignUpData({...signUpData, phone: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="address" className="text-black">Address</Label>
                  <Input
                    id="address"
                    type="text"
                    placeholder="Enter your address"
                    value={signUpData.address}
                    onChange={(e) => setSignUpData({...signUpData, address: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="role" className="text-black">Role</Label>
                  <Select value={signUpData.role} onValueChange={(value: 'customer' | 'employee' | 'admin') => setSignUpData({...signUpData, role: value})}>
                    <SelectTrigger className="bg-white border-gray-300 text-black">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-white border-gray-300">
                      <SelectItem value="customer">Customer</SelectItem>
                      <SelectItem value="employee">Employee</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-black">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a password"
                      value={signUpData.password}
                      onChange={(e) => setSignUpData({...signUpData, password: e.target.value})}
                      className="bg-white border-gray-300 text-black pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-black">Confirm Password</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm your password"
                      value={signUpData.confirmPassword}
                      onChange={(e) => setSignUpData({...signUpData, confirmPassword: e.target.value})}
                      className="bg-white border-gray-300 text-black pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-black text-white hover:bg-gray-800"
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating Account...' : 'Create Account'}
                </Button>
                
                <div className="text-center">
                  <span className="text-gray-600 text-sm">Already have an account? </span>
                  <button
                    type="button"
                    onClick={() => setViewState('signin')}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Sign in
                  </button>
                </div>
              </form>
            )}

            {/* Forgot Password Form */}
            {viewState === 'forgot' && (
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_name" className="text-black">Customer Name</Label>
                  <Input
                    id="customer_name"
                    type="text"
                    placeholder="Enter your customer name"
                    value={forgotData.customer_name}
                    onChange={(e) => setForgotData({...forgotData, customer_name: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-black">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={forgotData.email}
                    onChange={(e) => setForgotData({...forgotData, email: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-black text-white hover:bg-gray-800"
                  disabled={isLoading}
                >
                  {isLoading ? 'Sending...' : 'Send Temp Password'}
                </Button>
                
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setViewState('signin')}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Back to Sign In
                  </button>
                </div>
              </form>
            )}

            {/* Change Password Form */}
            {viewState === 'change' && (
              <form onSubmit={handleChangePassword} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_name" className="text-black">Customer Name</Label>
                  <Input
                    id="customer_name"
                    type="text"
                    placeholder="Enter your customer name"
                    value={changeData.customer_name}
                    onChange={(e) => setChangeData({...changeData, customer_name: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-black">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={changeData.email}
                    onChange={(e) => setChangeData({...changeData, email: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="temp_password" className="text-black">Temporary Password</Label>
                  <Input
                    id="temp_password"
                    type="password"
                    placeholder="Enter temporary password from email"
                    value={changeData.temp_password}
                    onChange={(e) => setChangeData({...changeData, temp_password: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="new_password" className="text-black">New Password</Label>
                  <Input
                    id="new_password"
                    type="password"
                    placeholder="Enter your new password"
                    value={changeData.new_password}
                    onChange={(e) => setChangeData({...changeData, new_password: e.target.value})}
                    className="bg-white border-gray-300 text-black"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-black text-white hover:bg-gray-800"
                  disabled={isLoading}
                >
                  {isLoading ? 'Changing Password...' : 'Change Password'}
                </Button>
                
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setViewState('signin')}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Back to Sign In
                  </button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
        
        {/* Back to Home Link */}
        <div className="text-center mt-6">
          <Link to="/" className="inline-flex items-center text-gray-600 hover:text-black transition-colors">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}