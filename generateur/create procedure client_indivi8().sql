create procedure client_indiviA()
    begin
    declare i int default 0;
    declare nbl int default 0;
    set nbl=(select count(*) from clients);
    label1:loop
     set i=i+1;
    Select * from clients where codeclient=i;
    if i<=nbl then ITERATE label1;
    end if;
    leave label1;
    end loop;
    end;
    //

    create procedure maboucle(pl int)
    begin
    label1:loop
    set pl=pl+1;
    select pl;
     if pl<10 then iterate label1;    
     end if;
     leave label1;
    end loop label1;
    end;
    //

    create procedure maboucle3(pl int)
    begin
    set @a=0;
    repeat 
    set @a=@a+1;
    select @a;
     until @a>pl
    end repeat;
    end;
    //
    
    create procedure maboucle4(pl int)
    begin
    set @a=0;
    while   pl>@a do
    set @a=@a+1;
    select @a;
    end while;
    end;
    //
    

create procedure increment_val2(para int)
    begin
    declare i int default 0;
     mouton:loop
     set i=i+1;
     select i;
     if i<para then iterate mouton;
     end if;
    leave mouton;
    end loop;
    end;//




    create procedure multiplication(para int)
    begin
    declare i int default 0;
    declare j int default 0;
     while j<para do
    set j=j+1;
     set i=0;
       while i<para do
     set i=i+1;
     select j,i,i*j;
     end while;
     select '*****';
     end while;
     end;//