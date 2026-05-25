import './globals.css';
import TopNav from '../components/layout/TopNav';

export const metadata = {
  title: 'Opptra Pricing Intelligence',
  description: 'Pricing intelligence dashboard for Buy Box optimization',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <TopNav />
        {children}
      </body>
    </html>
  );
}
