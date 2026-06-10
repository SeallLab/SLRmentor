import React from "react";
import styles from "./AboutUs.module.css";

export default function AboutUs({ onClose }) {
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
        <h2>About Us</h2>
        <div className={styles.section}>
          <img src="/LabLogo.png" alt="SEALL Logo" className={styles.image} />
          <div>
            <strong>PLURISE</strong>
            <p>
              The Plural Software Engineering for a Plural Society lab advances a 
              socio technical understanding of software engineering with emphasis on software processes and teamwork. 
              The lab conducts empirical studies on how human behavior, organizational context, 
              and development practices shape software systems, alongside research on software fairness, testing, and AI enabled technologies. 
              As software increasingly mediates work, education, and everyday life, the lab’s research 
              contributes evidence and conceptual frameworks that support software systems designed to account for the plurality of society.
            </p>
          </div>
        </div>
        <div className={styles.section}>
          <img src="/rodolfogil.jpeg" alt="Rodolfo Gil Portrait" className={styles.image} />
          <div>
            <strong>Rodolfo Gil Pereira (Undergraduate Research Assistant)</strong>
            <p>
              Rodolfo Gil Pereira is pursuing a degree in Software Engineering at the University of Calgary. 
              He is particularly interested in backend development 
              and software design, and he aspires to have a future career in the cloud industry.
            </p>
          </div>
        </div>
        <div className={styles.section}>
          <img src="/DrSouzaSantos.jpg" alt="Dr. Ronnie De Souza Santos Portrait" className={styles.image} />
          <div>
            <strong>Dr. Ronnie de Souza Santos, Ph.D.</strong>
            <p>
              Dr. Ronnie de Souza Santos is an Assistant Professor in Software Engineering at 
              the University of Calgary. He has an interest in the Human Aspects of Software 
              Engineering, the Software Development Process, Software Project Management, 
              Software Quality and Software Testing, EDI in the Software Industry, and Software 
              Fairness.
            </p>
          </div>
        </div>
        <button className={styles.closeButtonBottom} onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
