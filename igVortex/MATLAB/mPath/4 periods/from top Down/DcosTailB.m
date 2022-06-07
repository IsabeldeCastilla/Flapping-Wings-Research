function [ y ] = DcosTailB(t)
%Basic cos function (0<=t<=4) with a tail (4<=t<=8)

    if t <= 4.0
        y=-pi*sin(pi*t);
    else
        y=0;
    end
end

