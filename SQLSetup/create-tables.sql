CREATE TABLE Users (
   id         INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
   username   VARCHAR(32) NOT NULL UNIQUE,
   email      VARCHAR(32) NOT NULL UNIQUE,
   name       VARCHAR(64),
   profilePic VARCHAR(64),
   joinDate   DATETIME,
   password   VARCHAR(60),
   deleted    BOOLEAN DEFAULT FALSE
);

CREATE TABLE Groups (
   id          INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
   name        VARCHAR(64) NOT NULL,
   dateCreated DATETIME,
   img         VARCHAR(128),
   deleted     BOOLEAN DEFAULT FALSE
);

CREATE TABLE Bills (
   id          INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
   name        VARCHAR(128) NOT NULL,
   totalAmt    DECIMAL(8, 2),
   owner       INT UNSIGNED REFERENCES Users(id),
   groupId     INT UNSIGNED REFERENCES Groups(id),
   dueDate     DATE,
   complete    BOOLEAN DEFAULT FALSE,
   dateCreated DATETIME,
   deleted     BOOLEAN DEFAULT FALSE
);

CREATE TABLE UserBills (
   userId  INT UNSIGNED REFERENCES Users(id),
   billId  INT UNSIGNED REFERENCES Bills(id),
   paid    BOOLEAN DEFAULT FALSE,
   pending BOOLEAN DEFAULT FALSE
);

CREATE TABLE GroupMembers (
   userId  INT UNSIGNED REFERENCES Users(id),
   groupId INT UNSIGNED REFERENCES Groups(id),
   pending BOOLEAN DEFAULT FALSE
);

CREATE TABLE Tokens (
   `user`  INT UNSIGNED REFERENCES Users(id),
   token   CHAR(64) UNIQUE,
   expire  DATETIME,
   revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX TokenIndex ON Tokens(token, `user`);
