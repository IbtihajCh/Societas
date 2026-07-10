import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

const NAV_ITEMS = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/governance', label: 'Governance' },
  { href: '/policies', label: 'Policies' },
  { href: '/agents', label: 'Agents' },
];

export default function NavBar() {
  const router = useRouter();

  return (
    <nav
      style={{
        display: 'flex',
        gap: '1.5rem',
        padding: '0.75rem 2rem',
        borderBottom: '1px solid #eaeaea',
        backgroundColor: '#fafafa',
        fontFamily: 'system-ui',
      }}
    >
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          style={{
            color: router.pathname === item.href ? '#0070f3' : '#333',
            fontWeight: router.pathname === item.href ? 600 : 400,
            textDecoration: 'none',
            fontSize: '0.95rem',
            padding: '0.25rem 0',
            borderBottom:
              router.pathname === item.href ? '2px solid #0070f3' : '2px solid transparent',
          }}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
