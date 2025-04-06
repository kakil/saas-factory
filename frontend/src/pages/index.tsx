import { useEffect } from 'react';
import { useRouter } from 'next/router';

const IndexPage = () => {
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (token) {
      // If authenticated, redirect to dashboard
      router.push('/dashboard');
    } else {
      // Otherwise, redirect to login
      router.push('/auth/login');
    }
  }, [router]);

  return (
    <div className="loading-page">
      <div className="loading-container">
        <h2>Loading...</h2>
      </div>
    </div>
  );
};

export default IndexPage;
