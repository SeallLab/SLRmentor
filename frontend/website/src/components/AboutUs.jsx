import React from "react";
import styles from "./AboutUs.module.css";

export default function AboutUs({ onClose }) {
  return (
    <div className={styles.overlay} onClick={onClose}>
      <button className={styles.closeButton} onClick={onClose}>
        ✖
      </button>

      <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
        <h2>About Us</h2>
        <div className={styles.section}>
          <img src="/LabLogo.png" alt="SEALL Logo" className={styles.image} />
          <div>
            <strong>SE-ALL (Software Engineering for All Lab)</strong>
            <p>
              The SE-ALL (Software Engineering for All Lab) focuses on the human aspects
              of software engineering, including development practices, project management,
              software testing, fairness, and EDI. Understanding behaviors, cognitive skills,
              teamwork, and diverse user perspectives is vital for creating effective and
              innovative technology. As society becomes increasingly reliant on software 
              across work, education, politics, and leisure, and with the rise of AI-powered 
              systems, ensuring fairness and bias-free solutions in software is essential.
            </p>
          </div>
        </div>
        <div className={styles.section}>
          <img src="/rodolfogil.jpeg" alt="Rodolfo Gil Portrait" className={styles.image} />
          <div>
            <strong>Keeryn Johnson (Undergraduate Research Assistant)</strong>
            <p>
              Keeryn Johnson is currently studying at the University of Calgary for a Software
              Engineering Degree He has an interest in Robotics
              and Software Design, and hopes to work in the robotics industry in the future.
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
      </div>
    </div>
  );
}
