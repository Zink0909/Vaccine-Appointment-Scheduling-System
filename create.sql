CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Appointments (
    AppointmentID INTEGER PRIMARY KEY,
    Time date,
    CaregiverUsername varchar(255),
    PatientUsername varchar(255),
    VaccineName varchar(255),
    FOREIGN KEY (CaregiverUsername) REFERENCES Caregivers(Username),
    FOREIGN KEY (PatientUsername)   REFERENCES Patients(Username),
    FOREIGN KEY (VaccineName)       REFERENCES Vaccines(Name)
);
