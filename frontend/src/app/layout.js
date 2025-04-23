import '../styles/globals.css';

export const metadata = {
  title: 'AI Hire — Find the right job. Hire the right people. Instantly',
  description: 'AI powered job matching and application tracking for both applicants and recruiters',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="root-layout">
          {children}
        </div>
      </body>
    </html>
  );
}

