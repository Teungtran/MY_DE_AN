import fptShopLogo from '../assets/fpt-shop-logo.png';

export function FPTLogo() {
  return (
    <div className="flex items-center">
      {/* FPT Shop Logo - Using local image */}
      <img 
        src={fptShopLogo} 
        alt="FPT Shop" 
        className="h-12 w-auto object-contain"
        onError={(e) => {
          // Fallback to SVG if image fails to load
          const target = e.currentTarget;
          target.style.display = 'none';
          const fallback = target.nextElementSibling;
          if (fallback) fallback.classList.remove('hidden');
        }}
      />
      
      {/* Fallback SVG version of FPT Shop logo */}
      <svg 
        className="hidden h-10 w-auto"
        viewBox="0 0 500 100" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Simplified FPT Shop logo in SVG */}
        <rect x="10" y="10" width="80" height="80" rx="8" fill="#0066CC"/>
        <text x="30" y="65" fontFamily="Arial Black, sans-serif" fontSize="48" fontWeight="900" fill="white">F</text>
        
        <rect x="100" y="10" width="80" height="80" rx="8" fill="#FF6600"/>
        <text x="120" y="65" fontFamily="Arial Black, sans-serif" fontSize="48" fontWeight="900" fill="white">P</text>
        
        <rect x="190" y="10" width="80" height="80" rx="8" fill="#66CC33"/>
        <text x="212" y="65" fontFamily="Arial Black, sans-serif" fontSize="48" fontWeight="900" fill="white">T</text>
        
        <text x="290" y="60" fontFamily="Arial, sans-serif" fontSize="40" fontWeight="bold" fill="#000">
          Shop
        </text>
        <text x="405" y="60" fontFamily="Arial, sans-serif" fontSize="24" fill="#666">
          .com.vn
        </text>
      </svg>
    </div>
  );
}