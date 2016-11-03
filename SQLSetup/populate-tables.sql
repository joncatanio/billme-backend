INSERT INTO Users VALUES
   (NULL, 'joncatanio', 'joncatanio@gmail.com', 'Jon Catanio', '../imgs/user_profile/joncatanio.jpg', NOW(), '$2b$12$13tr4FhlBBSqSkaBOOI6x.VX8xIe5rj6sWzxjm6909bGUMsA5gx2i', 0),
   (NULL, 'obiwan', 'vaderslayer@gmail.com', 'Obi-Wan Kenobi', '../imgs/user_profile/obiwan.jpg', NOW(), '$2b$12$13tr4FhlBBSqSkaBOOI6x.VX8xIe5rj6sWzxjm6909bGUMsA5gx2i', 0)
;

INSERT INTO UserBills VALUES
   (1, 1, 0),
   (1, 2, 1),
   (1, 3, 0),
   (2, 2, 1),
   (2, 3, 1)
;

INSERT INTO Groups VALUES
   (NULL, 'Test Group', NOW(), '../imgs/group_pic/test_group.jpg', 0)
;

INSERT INTO GroupMembers VALUES
   (1, 1),
   (2, 1)
;

INSERT INTO Bills VALUES
   (NULL, 'PG&E', '47.23', 1, 1, NOW(), 0, NOW(), 0),
   (NULL, 'Water', '153.79', 2, 1, NOW(), 1, NOW(), 0),
   (NULL, 'Gas', '78.32', 2, 1, NOW(), 0, NOW(), 0)
;
