/* ============================================================
   Дополнение к архивной БД: администраторы и составы
   Firebird 2.5, диалект 3

   Выполнять в IBExpert (Tools -> Script Executive) поверх уже
   созданной базы DECREE_ARCHIVE.FDB.
   ============================================================ */

/* ---------- Администраторы ----------
   Хранится username из GROUPCONTENT. Админ входит своим обычным
   паролем от ГАС СДП; программа лишь проверяет наличие имени здесь. */

CREATE TABLE ADMINS (
    USERNAME VARCHAR(100) NOT NULL,
    CONSTRAINT PK_ADMINS PRIMARY KEY (USERNAME)
);

/* ---------- Составы (судья + помощники/секретари) ----------
   Все участники одного TEAM_NAME видят постановления друг друга.
   Один человек может состоять в нескольких составах. */

CREATE TABLE TEAM_MEMBERS (
    ID        INTEGER NOT NULL,
    TEAM_NAME VARCHAR(100) NOT NULL,
    USERNAME  VARCHAR(100) NOT NULL,
    CONSTRAINT PK_TEAM_MEMBERS PRIMARY KEY (ID),
    CONSTRAINT UQ_TEAM_MEMBER UNIQUE (TEAM_NAME, USERNAME)
);

CREATE GENERATOR GEN_TEAM_MEMBERS_ID;

SET TERM ^ ;
CREATE TRIGGER TEAM_MEMBERS_BI FOR TEAM_MEMBERS
ACTIVE BEFORE INSERT POSITION 0
AS
BEGIN
  IF (NEW.ID IS NULL) THEN
    NEW.ID = GEN_ID(GEN_TEAM_MEMBERS_ID, 1);
END^
SET TERM ; ^

CREATE INDEX IDX_TEAM_MEMBERS_USER ON TEAM_MEMBERS (USERNAME);
CREATE INDEX IDX_TEAM_MEMBERS_TEAM ON TEAM_MEMBERS (TEAM_NAME);

COMMIT;

/* ---------- Примеры ----------
   Назначить администратора (подставьте реальный username из GROUPCONTENT):

   INSERT INTO ADMINS (USERNAME) VALUES ('Админ');
   COMMIT;

   Состав можно завести и вручную, без программы:

   INSERT INTO TEAM_MEMBERS (TEAM_NAME, USERNAME) VALUES ('Состав Кондратова', 'Кондратов');
   INSERT INTO TEAM_MEMBERS (TEAM_NAME, USERNAME) VALUES ('Состав Кондратова', 'Иванова');
   COMMIT;
*/
