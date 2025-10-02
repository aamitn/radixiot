import React from "react";

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white p-4 mt-auto">
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
        <span className="text-sm">&copy; {new Date().getFullYear()} Radix IoT Platform. All rights reserved.</span>
        <div className="flex space-x-4 mt-2 md:mt-0">
          <a href="https://bitmutex.com" target="_blank" rel="noopener noreferrer" className="hover:underline">
            Bitmutex
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
