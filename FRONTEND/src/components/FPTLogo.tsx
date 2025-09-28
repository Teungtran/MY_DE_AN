import React from 'react';
import { ImageWithFallback } from './figma/ImageWithFallback';

export function FPTLogo() {
  return (
    <div className="flex items-center space-x-4">
      {/* FPT Shop Logo */}
      <div className="flex items-center space-x-2">
        <ImageWithFallback
          src="https://images.unsplash.com/photo-1659293641659-4401c4472a4e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxGUFQlMjBjb3Jwb3JhdGlvbiUyMGxvZ298ZW58MXx8fHwxNzU4NzI2Njk5fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
          alt="FPT Shop Logo"
          className="w-10 h-10 object-contain"
        />
        <div className="flex flex-col">
          <span className="font-bold text-lg text-orange-600">FPT</span>
          <span className="text-xs text-gray-600 -mt-1">Shop.vn</span>
        </div>
      </div>
      
      <div className="border-l border-gray-300 pl-4">
        <h1 className="text-xl font-bold text-black">SAGE</h1>
        <p className="text-xs text-gray-600">AI Assistant</p>
      </div>
    </div>
  );
}