import React from 'react';
import sageLogoImage from 'figma:asset/e22d969d9d08fe5807592bcbedbd8f802ee67db1.png';

export function FPTLogo() {
  return (
    <div className="flex items-center">
      <img
        src={sageLogoImage}
        alt="SAGE - AI Platform for Modern Retail"
        className="h-12 w-auto object-contain"
      />
    </div>
  );
}