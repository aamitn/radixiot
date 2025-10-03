import React from "react";
import { Link } from "react-router-dom";

const Header = () => {
  return (
    <header className="sticky top-0 bg-slate-800/70 shadow-md z-50">
      <div className="container mx-auto flex items-center justify-between px-6 py-3">
        {/* Logo linking to home */}
        <Link to="/">
          <img
            src="/logo.png"
            alt="Radix-IoT Logo"
            className="h-10 w-auto"
          />
        </Link>

        {/* Navigation */}
        <nav className="space-x-4">
          <Link
            to="/"
            className="text-gray-400 hover:text-primary font-medium"
          >
            Home
          </Link>
          <Link
            to="/dashboard"
            className="text-gray-400 hover:text-primary font-medium"
          >
            Dashboard
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
