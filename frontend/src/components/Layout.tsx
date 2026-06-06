import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { useInactivityTimer } from '../hooks/useInactivityTimer';

export function Layout() {
  useInactivityTimer();
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
