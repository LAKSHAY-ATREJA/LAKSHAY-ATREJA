export type Card={id:string; title:string; column:string; version:number};
export type Operation={type:"create"|"move"|"rename"; cardId:string; baseVersion:number; title?:string; column?:string};
export function apply(cards:Map<string,Card>, op:Operation):Card{
  const current=cards.get(op.cardId);
  if(op.type==="create"){
    if(current) throw new Error("card already exists");
    const card={id:op.cardId,title:op.title??"Untitled",column:op.column??"todo",version:1}; cards.set(card.id,card); return card;
  }
  if(!current) throw new Error("card not found");
  if(current.version!==op.baseVersion) throw new Error("version conflict");
  const next={...current,version:current.version+1,title:op.title??current.title,column:op.column??current.column}; cards.set(next.id,next); return next;
}
