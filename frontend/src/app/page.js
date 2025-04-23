import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="homepage">
      <div className="container">
        <h2 className="heading">
          Who are you?
        </h2>

        <div className="button-group">
          <Link href="/applicant" className="btn btn-applicant">
            Applicant
          </Link>

          <Link href="/recruiter" className="btn btn-recruiter">
            Recruiter
          </Link>
        </div>

        <p className="subtext">
          Select your role to get started
        </p>
      </div>
    </main>
  );
}
