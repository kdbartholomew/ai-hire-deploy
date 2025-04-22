// File: app/page.js
import Link from 'next/link'; // Import the Next.js Link component for client-side navigation

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-100">
      <div className="text-center max-w-md">

        <h2 className="text-3xl md:text-4xl font-semibold mb-10 text-gray-800">
          Who are you?
        </h2>

        <div className="flex flex-col sm:flex-row justify-center gap-6">
          {/* Applicant Button */}
          <Link
            href="/applicant" // Links to the page rendered by app/applicant/page.js
            className="inline-block px-10 py-4 bg-blue-600 text-white text-lg font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out"
          >
            Applicant
          </Link>

          {/* Recruiter Button */}
          <Link
            href="/recruiter" // Links to the page rendered by app/recruiter/page.js (You'll need to create this)
            className="inline-block px-10 py-4 bg-green-600 text-white text-lg font-medium rounded-md shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-150 ease-in-out"
          >
            Recruiter
          </Link>
        </div>

        <p className="text-sm text-gray-500 mt-12">
          Select your role to get started.
        </p>

      </div>
    </main>
  );
}