import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import styles from './NavBar.module.css';

const NAV_GROUPS = [
  {
    label: 'Register',
    items: [
      { href: '/', label: 'Overview' },
      { href: '/dashboard', label: 'Dashboard' },
      { href: '/governance', label: 'Governance' },
    ],
  },
  {
    label: 'Records',
    items: [
      { href: '/policies', label: 'Policies' },
      { href: '/agents', label: 'Citizens' },
    ],
  },
];

export default function NavBar() {
  const router = useRouter();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.crest}>S</div>
        <div>
          <div className={styles.brandName}>Societas</div>
          <div className={`${styles.brandSub} ${styles.sc}`}>World Ledger</div>
        </div>
      </div>

      {NAV_GROUPS.map((group) => (
        <div key={group.label} className={styles.navGroup}>
          <div className={`${styles.navLabel} ${styles.sc}`}>
            {group.label}
          </div>
          {group.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.sc} ${
                router.pathname === item.href
                  ? `${styles.navItem} ${styles.navItemActive}`
                  : styles.navItem
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      ))}

      <div className={styles.sidebarFooter}>
        <div className={`${styles.footerLabel} ${styles.sc}`}>
          vLLM Cluster
        </div>
        <div className={styles.footerVal}>
          <span className={styles.stampDot} />
          3 models attending
        </div>
      </div>
    </aside>
  );
}