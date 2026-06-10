import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './NavBar.module.css';
import PdfPopup from './PdfPopup';
import AboutUs from './AboutUs';

export default function NavBar({ startTour }) {
  const [showPdfPopup, setShowPdfPopup] = useState(false);
  const [showAboutUs, setShowAboutUs] = useState(false);

  return (
    <>
      <nav className={styles.navbar}>
        <Link
          to="/"
          className={styles.homeLink}
          id="nav-home"
        >
          <img
            src="/bita_recolor_with_hat.png"
            alt="SLRmentor Logo"
            className={styles.logo}
          />
          <span className={styles.title}>SLRmentor</span>
        </Link>

        <div className={styles.navButtons}>
          <button
            id="nav-about-slrs"
            className={styles.navButton}
            onClick={() => setShowPdfPopup(prev => !prev)}
          >
            About SLRs
          </button>

          <button
            id="nav-how-to"
            className={styles.navButton}
            onClick={() => {
              console.log("How to Use clicked. startTour=", startTour);
              if (typeof startTour === "function") startTour();
              else console.error("startTour prop is not a function");
            }}
          >
            How to Use SLRmentor
          </button>

          <button
            id="nav-about-us"
            className={styles.navButton}
            onClick={() => setShowAboutUs(prev => !prev)}
          >
            About Us
          </button>
        </div>
      </nav>

      {showPdfPopup && (
        <PdfPopup
          file="/SEALL- SLRMentor Student Guide.pdf"
          onClose={() => setShowPdfPopup(false)}
        />
      )}

      {showAboutUs && (
        <AboutUs
          onClose={() => setShowAboutUs(false)}
        />
      )}
    </>
  );
}
